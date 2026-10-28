'use strict';
/* Synchronous psql emulation on PGlite (PostgreSQL 16 compiled to WASM) for machines without a PostgreSQL server.
   Usage: NODE_PATH=<dir containing @electric-sql/pglite@0.2.x> CODIS_PSQL_MODULE=tests/pglite_bridge.js node tests/harness.js
   Exports psqlSync(args, input) -> {status, stdout, stderr}. Supports the psql flags the tests use:
   -q -A -t -X -U -d -v ON_ERROR_STOP=1 -c <sql> -f - ; and the meta-commands \set ON_ERROR_STOP and \pset (ignored).
   Each call is a fresh session (DISCARD ALL), like a new psql process. "drop/create database X" recreates an in-memory db. */
const { Worker, isMainThread, parentPort, workerData, MessageChannel, receiveMessageOnPort } = require('worker_threads');

if (isMainThread) {
  let w, port, sig;
  function start() {
    const ch = new MessageChannel(); port = ch.port1;
    sig = new Int32Array(new SharedArrayBuffer(4));
    w = new Worker(__filename, { workerData: { port: ch.port2, sig }, transferList: [ch.port2] });
    w.unref(); port.unref();
  }
  module.exports.psqlSync = function (args, input) {
    if (!w) start();
    Atomics.store(sig, 0, 0);
    w.postMessage({ args, input: input || '' });
    while (Atomics.wait(sig, 0, 0, 120000) === 'timed-out') throw new Error('pglite bridge timeout');
    const m = receiveMessageOnPort(port);
    if (!m) throw new Error('pglite bridge: no reply');
    return m.message;
  };
} else {
  const { PGlite } = require('@electric-sql/pglite');
  const { port, sig } = workerData;
  const dbs = {};
  const raw = x => x;
  const parsers = {};
  [16, 17, 20, 21, 23, 26, 114, 700, 701, 1082, 1114, 1184, 1700, 3802].forEach(o => { parsers[o] = raw; });
  async function db(name) { if (!dbs[name]) { dbs[name] = new PGlite({ parsers }); await dbs[name].waitReady; } return dbs[name]; }

  function split(sql) { // top-level ';' split aware of quotes, comments and dollar quotes
    const out = []; let cur = '', i = 0;
    while (i < sql.length) {
      const c = sql[i], n = sql[i + 1];
      if (c === '-' && n === '-') { const e = sql.indexOf('\n', i); const j = e < 0 ? sql.length : e; cur += sql.slice(i, j); i = j; continue; }
      if (c === '/' && n === '*') { const e = sql.indexOf('*/', i + 2); const j = e < 0 ? sql.length : e + 2; cur += sql.slice(i, j); i = j; continue; }
      if (c === "'" || c === '"') { let j = i + 1; while (j < sql.length) { if (sql[j] === c) { if (sql[j + 1] === c) { j += 2; continue; } break; } j++; } cur += sql.slice(i, j + 1); i = j + 1; continue; }
      if (c === '$') { const m = /^\$[A-Za-z_]*\$/.exec(sql.slice(i)); if (m) { const e = sql.indexOf(m[0], i + m[0].length); const j = e < 0 ? sql.length : e + m[0].length; cur += sql.slice(i, j); i = j; continue; } }
      if (c === ';') { if (cur.trim()) out.push(cur); cur = ''; i++; continue; }
      cur += c; i++;
    }
    if (cur.trim()) out.push(cur);
    return out;
  }

  async function run({ args, input }) {
    let dbName = 'postgres', stop = false, tuplesOnly = false, unaligned = false; const units = [];
    for (let i = 0; i < args.length; i++) {
      const a = args[i];
      if (a === '-d') dbName = args[++i];
      else if (a === '-U') i++;
      else if (a === '-v') { const v = args[++i]; if (/^ON_ERROR_STOP=/i.test(v)) stop = !/=(0|off|false)$/i.test(v); }
      else if (a === '-c') units.push(args[++i]);
      else if (a === '-f') { const f = args[++i]; units.push(f === '-' ? input : require('fs').readFileSync(f, 'utf8')); }
      else if (/^-[qAtX]+$/.test(a)) { if (a.includes('t')) tuplesOnly = true; if (a.includes('A')) unaligned = true; }
      else return { status: 1, stdout: '', stderr: 'pglite bridge: unsupported arg ' + a };
    }
    let stdout = '', stderr = '';
    const d = await db(dbName);
    await d.exec('reset role'); await d.exec('discard all'); // PGlite keeps the role across DISCARD ALL
    for (const u of units) {
      const lines = u.split('\n'); const kept = [];
      for (const l of lines) {
        const m = /^\s*\\(\w+)\s*(.*)$/.exec(l);
        if (!m) { kept.push(l); continue; }
        kept.push('');
        if (m[1] === 'set' && /^ON_ERROR_STOP\b/i.test(m[2])) stop = !/\b(0|off|false)\s*$/i.test(m[2]);
      }
      for (const stmt of split(kept.join('\n'))) {
        const dm = /^\s*(drop|create)\s+database\s+(if\s+exists\s+)?(\w+)\s*$/i.exec(stmt);
        if (dm) { const k = dm[3]; if (dm[1].toLowerCase() === 'drop') { if (dbs[k]) { await dbs[k].close(); delete dbs[k]; } } else await db(k); continue; }
        try {
          const res = await d.exec(stmt, { parsers });
          for (const r of res) {
            if (!r.fields || !r.fields.length) continue;
            const names = r.fields.map(f => f.name);
            if (!tuplesOnly) stdout += names.join(unaligned ? '|' : ' | ') + '\n';
            for (const row of r.rows) stdout += names.map(n => row[n] === null || row[n] === undefined ? '' : String(row[n])).join(unaligned ? '|' : ' | ') + '\n';
          }
        } catch (e) {
          stderr += 'psql:<stdin>: ERROR:  ' + (e.message || String(e)) + '\n';
          if (stop) return { status: 3, stdout, stderr };
        }
      }
    }
    return { status: 0, stdout, stderr };
  }

  parentPort.on('message', async msg => {
    let r; try { r = await run(msg); } catch (e) { r = { status: 2, stdout: '', stderr: 'pglite bridge: ' + (e && e.message || e) }; }
    port.postMessage(r);
    Atomics.store(sig, 0, 1); Atomics.notify(sig, 0);
  });
}
