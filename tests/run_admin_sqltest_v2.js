'use strict';
/* Admin v2 SQL tests: stub.sql → codis_supabase_setup.sql → codis_admin.sql → codis_admin_v2.sql (twice = idempotency) → admin_sqltest_v2.sql
   Usage: NODE_PATH=<dir containing @electric-sql/pglite@0.2.x> node tests/run_admin_sqltest_v2.js   (writes tests/admin_sql_v2_results.txt)
   A row fails if it says UNEXPECTED (a denial test succeeded) or if a count/shape row differs from EXPECT below. */
const fs = require('fs'), path = require('path'); const ROOT = path.join(__dirname, '..');
const { psqlSync } = require('./pglite_bridge.js');
const read = f=>fs.readFileSync(path.join(ROOT, f), 'utf8');
const step = (name, args, input)=>{ const r = psqlSync(args, input); if(r.status !== 0){ console.log('FAIL', name, r.stderr); process.exit(1); } return r; };
const run = (name, sql)=>step(name, ['-q', '-v', 'ON_ERROR_STOP=1', '-d', 'codis_a', '-f', '-'], sql);
step('create db', ['-q', '-c', 'drop database if exists codis_a', '-c', 'create database codis_a']);
run('stub.sql', read('tests/stub.sql'));
run('auth.users extra columns', "alter table auth.users add column if not exists raw_user_meta_data jsonb default '{}'::jsonb, add column if not exists created_at timestamptz default now(), add column if not exists last_sign_in_at timestamptz, add column if not exists banned_until timestamptz;");
run('setup.sql', read('sql/codis_supabase_setup.sql'));
run('admin.sql', read('sql/codis_admin.sql'));
run('admin_v2.sql', read('sql/codis_admin_v2.sql'));
run('admin_v2.sql again (idempotent)', read('sql/codis_admin_v2.sql'));
const r = step('admin_sqltest_v2.sql', ['-q', '-A', '-t', '-d', 'codis_a', '-f', '-'], read('tests/admin_sqltest_v2.sql'));
const rows = r.stdout.split('\n').filter(l=>l.includes('|') && /^B\d/.test(l)).map(l=>{ const i = l.indexOf('|'); return [l.slice(0, i), l.slice(i + 1)]; });
const w = Math.max(...rows.map(x=>x[0].length));
const out = rows.map(([t, v])=>' ' + t.padEnd(w) + ' | ' + v).join('\n') + '\n';
fs.writeFileSync(path.join(__dirname, 'admin_sql_v2_results.txt'), out);
process.stdout.write(out);
const EXPECT = {
  'B3 first send creates 3 rows, not duplicate': /"n": 3[\s\S]*"created": 3[\s\S]*"duplicate": false/, 'B3 retry SAME request: duplicate=true, nothing new': /"created": 0[\s\S]*"duplicate": true/,
  'B3 rows after retry (must be 3: A,B,C)': /^3$/, 'B3 audit rows for the grant (must be 1)': /^1$/, 'B3 list pending (must be 4)': /^4$/, 'B3 list search adj (must be 1)': /^1$/, 'B3 messages rows (must be 1)': /^1$/,
  'B3 message v2 retry duplicate': /"duplicate": true/, 'B4 B sees only own rows (must be 2)': /^2$/, 'B4 B acks own gifts (must be 2)': /^2$/, 'B5 applied (must be 2)': /^2$/, 'B5 pending before cancel (must be 2: A,C)': /^2$/, 'B5 cancel one pending': /^true$/,
  'B5 cancelled (must be 1)': /^1$/, 'B5 pending after cancel (must be 1)': /^1$/ };
let bad = rows.filter(x=>/UNEXPECTED/.test(x[1])).length;
Object.keys(EXPECT).forEach(k=>{ const row = rows.find(x=>x[0].trim() === k); if(!row){ console.log('MISSING ROW', k); bad++; } else if(!EXPECT[k].test(row[1].trim())){ console.log('MISMATCH', k, '=>', row[1].trim()); bad++; } });
console.log('\nrows:', rows.length, ' failures:', bad, r.stderr ? ('\nstderr:\n' + r.stderr) : '');
process.exit(bad ? 1 : 0);
