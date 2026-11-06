import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const P = process.argv[2];
const db = new PGlite();
const out = []; const T = (n, ok, i='')=>out.push([ok ? 'PASS' : 'FAIL', n, i]);
await db.exec(fs.readFileSync(P + '/tests/stub.sql', 'utf8'));
await db.exec('create role service_role nologin; grant usage on schema public to service_role;');
await db.exec(fs.readFileSync(P + '/sql/codis_supabase_setup.sql', 'utf8'));
{ const full = fs.readFileSync(P + '/sql/codis_push.sql', 'utf8'); const cut = full.indexOf('-- ---------- 5'); await db.exec(cut > 0 ? full.slice(0, cut) : full); }
await db.exec(fs.readFileSync(P + '/sql/codis_push_v2.sql', 'utf8'));
await db.exec(fs.readFileSync(P + '/sql/codis_push_v2.sql', 'utf8'));
T('v2 applies twice (idempotent)', true);
const A = '11111111-1111-1111-1111-111111111111', B = '22222222-2222-2222-2222-222222222222';
await db.exec(`insert into auth.users(id,email) values ('${A}','a@x'),('${B}','b@x')`);
async function as(role, uid, sql){ await db.exec(`set role ${role}; select set_config('request.jwt.claim.sub', '${uid || ''}', false);`); try{ return await db.query(sql); } finally { await db.exec('reset role'); } }
async function fails(role, uid, sql){ try{ await as(role, uid, sql); return null; } catch(e){ return e.message; } }
await as('authenticated', A, `select push_subscribe('https://push.example.com/ep/A1', '${'B'.repeat(87)}', '${'a'.repeat(22)}', 'ua')`);
await as('authenticated', A, `select push_schedule('ev_hn231a2b3c4d20261107', now() + interval '3 days', 'تذكير', 'body')`);
T('5-day-ahead reminder accepted (v2 window)', (await db.query(`select count(*)::int n from push_timers where user_id='${A}'`)).rows[0].n === 1);
await as('authenticated', A, `select push_schedule('ev_hn231a2b3c4d20261107', now() + interval '3 days 1 hour', 'تذكير', 'new body')`);
T('same id updates (no duplicate row)', (await db.query(`select count(*)::int n, max(body) b from push_timers`)).rows[0].n === 1);
T('beyond 8 days rejected', /invalid time/.test(await fails('authenticated', A, `select push_schedule('ev_far000001', now() + interval '9 days', 'x', 'y')`) || ''));
T('underscore ids rejected', /invalid event id/.test(await fails('authenticated', A, `select push_schedule('ev_h_bad_1234', now() + interval '1 day', 'x', 'y')`) || ''));
await as('authenticated', B, `select push_schedule('ev_hn231a2b3c4d20261107', now() + interval '2 days', 'hijack', 'hijack')`);
T('another user cannot take over the id', (await db.query(`select user_id::text u, body from push_timers where event_id='ev_hn231a2b3c4d20261107'`)).rows[0].u === A);
await as('authenticated', A, `select push_schedule('ev_dueeeee01', now() - interval '5 seconds', 'x', 'due')`);
const c = (await as('service_role', null, `select * from push_claim_due(50)`)).rows;
T('claim returns only the due one, once', c.length === 1);
const c2 = (await as('service_role', null, `select * from push_claim_due(50)`)).rows;
T('no resend on the next minute', c2.length === 0);
await as('authenticated', A, `select push_cancel('ev_hn231a2b3c4d20261107')`);
await as('authenticated', A, `select push_schedule('ev_hn231a2b3c4d20261107', now() - interval '2 seconds', 'x', 'again')`);
T('cancelled + rescheduled reminder fires again', (await as('service_role', null, `select * from push_claim_due(50)`)).rows.length === 1);
console.log(out.map(x=>x.join(' | ')).join('\n')); console.log('FAILS', out.filter(x=>x[0]==='FAIL').length);
