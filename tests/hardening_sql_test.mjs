/* CODIS hardening v38 SQL test (sql/codis_hardening_v38.sql) on PGlite — isolated in-memory Postgres, no production access.
   node tests/hardening_sql_test.mjs <project root>   (needs: npm i @electric-sql/pglite in a scratch folder) */
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const P = process.argv[2];
const db = new PGlite();
const out = []; const T = (n, ok, i='')=>out.push([ok ? 'PASS' : 'FAIL', n, i]);
await db.exec(fs.readFileSync(P + '/tests/stub.sql', 'utf8'));
await db.exec('create role service_role nologin; grant usage on schema public to service_role;');
/* Vault stub (Supabase-managed in production) */
await db.exec(`create schema vault; create table vault.secrets(name text primary key, secret text);
  create view vault.decrypted_secrets as select name, secret as decrypted_secret from vault.secrets;
  create function vault.create_secret(s text, n text) returns uuid language sql as $$ insert into vault.secrets values (n, s); select gen_random_uuid(); $$;`);
await db.exec(fs.readFileSync(P + '/sql/codis_supabase_setup.sql', 'utf8'));
{ const full = fs.readFileSync(P + '/sql/codis_push.sql', 'utf8'); const cut = full.indexOf('create extension if not exists pg_cron'); await db.exec(cut > 0 ? full.slice(0, cut) : full); }
await db.exec(fs.readFileSync(P + '/sql/codis_push_v2.sql', 'utf8'));
const H = fs.readFileSync(P + '/sql/codis_hardening_v38.sql', 'utf8');
await db.exec(H); await db.exec(H);
T('hardening applies twice (idempotent)', true);
const defs = (await db.query(`select p.proname, p.proconfig from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname = 'public' and p.proname like 'push_%' and p.prosecdef`)).rows;
T('all 9 SECURITY DEFINER push functions pin search_path to empty', defs.length === 9 && defs.every(d=>(d.proconfig || []).some(c=>c === 'search_path=""')), JSON.stringify(defs.map(d=>d.proname + ':' + d.proconfig)));
const A = '11111111-1111-1111-1111-111111111111', B = '22222222-2222-2222-2222-222222222222';
await db.exec(`insert into auth.users(id,email) values ('${A}','a@x'),('${B}','b@x')`);
async function as(role, uid, sql){ await db.exec(`set role ${role}; select set_config('request.jwt.claim.sub', '${uid || ''}', false);`); try{ return await db.query(sql); } finally { await db.exec('reset role'); } }
async function fails(role, uid, sql){ try{ await as(role, uid, sql); return null; } catch(e){ return e.message; } }
const K1 = 'B'.repeat(87), A1 = 'a'.repeat(22), K2 = 'C'.repeat(87), A2 = 'c'.repeat(22), EP = 'https://push.example.com/ep/victim';
await as('authenticated', A, `select push_subscribe('${EP}', '${K1}', '${A1}', 'ua-A')`);
const owner = async()=>(await db.query(`select user_id::text u from push_subscriptions where endpoint='${EP}'`)).rows[0].u;
T('subscribe works (owner A)', await owner() === A);
await as('authenticated', B, `select push_subscribe('${EP}', '${K2}', '${A2}', 'attacker')`);
T('TAKEOVER BLOCKED: B with only the endpoint URL cannot rebind A\'s device', await owner() === A && (await db.query(`select p256dh from push_subscriptions where endpoint='${EP}'`)).rows[0].p256dh === K1);
await as('authenticated', B, `select push_subscribe('${EP}', '${K1}', '${A1}', 'same device, account switch')`);
T('genuine account switch on the same device (same keys) still works', await owner() === B);
await as('authenticated', B, `select push_subscribe('${EP}', '${K2}', '${A2}', 'B refreshes own keys')`);
T('owner can refresh its own subscription keys', (await db.query(`select p256dh from push_subscriptions where endpoint='${EP}'`)).rows[0].p256dh === K2);
T('anon cannot subscribe', !!await fails('anon', null, `select push_subscribe('https://x.example/e', '${K1}', '${A1}', 'u')`));
/* behaviour regression (same as v2 test) */
await as('authenticated', A, `select push_schedule('ev_aaaaaa1', now() + interval '3 days', 't', 'b')`);
T('schedule within 8 days accepted', (await db.query(`select count(*)::int n from push_timers where user_id='${A}'`)).rows[0].n === 1);
T('beyond 8 days rejected', /invalid time/.test(await fails('authenticated', A, `select push_schedule('ev_far0001', now() + interval '9 days', 'x', 'y')`) || ''));
await as('authenticated', B, `select push_schedule('ev_aaaaaa1', now() + interval '1 day', 'hijack', 'hijack')`);
T('another user cannot take over a timer id', (await db.query(`select user_id::text u from push_timers where event_id='ev_aaaaaa1'`)).rows[0].u === A);
await as('authenticated', A, `select push_schedule('ev_due0001', now() - interval '5 seconds', 'x', 'due')`);
T('service_role claims the due reminder', (await as('service_role', null, `select * from push_claim_due(50)`)).rows.length >= 0 && (await db.query(`select count(*)::int n from push_timers where event_id='ev_due0001' and sent_at is not null`)).rows[0].n === 1);
T('no resend after claim', (await as('service_role', null, `select * from push_claim_due(50)`)).rows.length === 0);
T('authenticated cannot call push_claim_due', !!await fails('authenticated', A, `select * from push_claim_due(5)`));
T('authenticated cannot read VAPID private key (push_keys)', !!await fails('authenticated', A, `select * from push_keys()`));
await as('service_role', null, `select push_keys_init('${'P'.repeat(87)}', '${'Q'.repeat(43)}')`);
T('anon reads only the public key', (await as('anon', null, `select push_vapid_public() k`)).rows[0].k === 'P'.repeat(87));
T('keys created once, never replaced', (await as('service_role', null, `select push_keys_init('${'X'.repeat(87)}', '${'Y'.repeat(43)}') r`)).rows[0].r === false);
T('push_timers.user_id index exists', (await db.query(`select count(*)::int n from pg_indexes where indexname='push_timers_user_id_idx'`)).rows[0].n === 1);
console.log(out.map(x=>x.join(' | ')).join('\n')); console.log('FAILS', out.filter(x=>x[0]==='FAIL').length);
