/* CODIS push SQL test (sql/codis_push.sql) on PGlite: node tests/push_sql_test.mjs <project root>  — needs: npm i @electric-sql/pglite (outside the repo is fine, run with that node_modules on the path) */
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const P = process.argv[2];
const db = new PGlite();
const out = []; const T = (n, ok, i='')=>out.push([ok ? 'PASS' : 'FAIL', n, i]);
await db.exec(fs.readFileSync(P + '/tests/stub.sql', 'utf8'));
await db.exec('create role service_role nologin; grant usage on schema public to service_role;');
await db.exec(fs.readFileSync(P + '/sql/codis_supabase_setup.sql', 'utf8'));
await db.exec(fs.readFileSync(P + '/sql/codis_push.sql', 'utf8'));
await db.exec(fs.readFileSync(P + '/sql/codis_push.sql', 'utf8'));   // idempotent
T('schema applies twice (idempotent)', true);
const A = '11111111-1111-1111-1111-111111111111', B = '22222222-2222-2222-2222-222222222222';
await db.exec(`insert into auth.users(id,email) values ('${A}','a@x'),('${B}','b@x')`);
async function as(role, uid, sql){ await db.exec(`set role ${role}; select set_config('request.jwt.claim.sub', '${uid || ''}', false);`); try{ return await db.query(sql); } finally { await db.exec('reset role;'); } }
async function fails(role, uid, sql){ try{ await as(role, uid, sql); return null; } catch(e){ return e.message; } }
const ep = 'https://push.example.com/ep/A1', key = 'B'.repeat(87), auth = 'a'.repeat(22);
await as('authenticated', A, `select push_subscribe('${ep}', '${key}', '${auth}', 'ua')`);
T('user A subscribes', (await db.query(`select count(*)::int n from push_subscriptions where user_id='${A}'`)).rows[0].n === 1);
T('anon cannot subscribe', !!(await fails('anon', '', `select push_subscribe('${ep}2', '${key}', '${auth}', 'ua')`)));
T('bad subscription rejected', /invalid/.test(await fails('authenticated', A, `select push_subscribe('http://insecure', '${key}', '${auth}', null)`) || ''));
T('authenticated cannot read subscriptions table', /permission denied/.test(await fails('authenticated', A, 'select * from push_subscriptions') || ''));
T('authenticated cannot read timers table', /permission denied/.test(await fails('authenticated', A, 'select * from push_timers') || ''));
await as('authenticated', A, `select push_schedule('ev_abc123', now() - interval '5 seconds', 'انتهى الوقت', 'انتهى وقت مكافأة ساعة سوشل ميديا')`);
await as('authenticated', A, `select push_schedule('ev_later99', now() + interval '1 hour', 'انتهى الوقت', 'later')`);
await as('authenticated', A, `select push_schedule('ev_cancel1', now() - interval '5 seconds', 'x', 'cancel me')`);
await as('authenticated', A, `select push_cancel('ev_cancel1')`);
T('bad event id rejected', /invalid event id/.test(await fails('authenticated', A, `select push_schedule('DROP', now(), 'x', 'y')`) || ''));
T('far-future time rejected', /invalid time/.test(await fails('authenticated', A, `select push_schedule('ev_far0001', now() + interval '3 days', 'x', 'y')`) || ''));
await as('authenticated', B, `select push_schedule('ev_abc123', now() + interval '2 hours', 'hijack', 'hijack')`);
await as('authenticated', B, `select push_cancel('ev_later99')`);
const r1 = (await db.query(`select user_id, title, cancelled_at from push_timers where event_id in ('ev_abc123','ev_later99') order by event_id`)).rows;
T("B cannot overwrite or cancel A's events", r1.every(r=>r.user_id === A && r.title !== 'hijack' && !r.cancelled_at), JSON.stringify(r1));
T('authenticated cannot claim due pushes', /permission denied/.test(await fails('authenticated', A, 'select * from push_claim_due(10)') || ''));
const c1 = (await as('service_role', '', 'select * from push_claim_due(10)')).rows;
T('service claims only the due, uncancelled event with its device', c1.length === 1 && c1[0].event_id === 'ev_abc123' && c1[0].endpoint === ep, JSON.stringify(c1.map(r=>r.event_id)));
const c2 = (await as('service_role', '', 'select * from push_claim_due(10)')).rows;
T('second cron run claims nothing (sent once)', c2.length === 0);
await as('authenticated', A, `select push_cancel('ev_abc123')`);
T('cancel after send does not reopen it', (await db.query(`select sent_at is not null s, cancelled_at is null c from push_timers where event_id='ev_abc123'`)).rows[0].c === true);
await as('service_role', '', `select push_drop_endpoint('${ep}')`);
T('service can drop a gone endpoint', (await db.query(`select count(*)::int n from push_subscriptions`)).rows[0].n === 0);
out.forEach(r=>console.log(r.join('  ')));
const bad = out.filter(r=>r[0] === 'FAIL').length; console.log(bad ? 'FAILED ' + bad : 'ALL ' + out.length + ' PASSED'); process.exit(bad ? 1 : 0);
