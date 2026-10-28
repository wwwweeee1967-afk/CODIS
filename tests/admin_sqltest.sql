\set ON_ERROR_STOP off
\pset pager off
-- Admin powers isolation tests (run after stub.sql + codis_supabase_setup.sql + codis_admin.sql)
create temp table res(t text, r text);
grant all on res to anon, authenticated;
insert into auth.users(id,email,raw_user_meta_data,created_at,last_sign_in_at) values
 ('aaaaaaaa-0000-0000-0000-000000000001','admin@x','{"full_name":"Admin"}',now(),now()),
 ('bbbbbbbb-0000-0000-0000-000000000002','b@x','{"full_name":"<img src=x onerror=alert(1)>","role":"admin","is_admin":true}',now(),now()),
 ('cccccccc-0000-0000-0000-000000000003','c@x','{}',now(),null);
insert into public.admins(user_id) values ('aaaaaaaa-0000-0000-0000-000000000001');
insert into public.progress(user_id,data) values
 ('bbbbbbbb-0000-0000-0000-000000000002','{"wallet":{"balance":50,"silver":{"balance":7}},"profile":{"name":"Bee","photo":"data:big"}}'),
 ('cccccccc-0000-0000-0000-000000000003','{"wallet":{"balance":"not a number","silver":{"balance":1e40}}}');

-- helper: expect denial
create or replace function pg_temp.deny(t text, q text) returns void language plpgsql as $$
begin
  begin execute q; insert into res values(t, 'UNEXPECTED ok');
  exception when others then insert into res values(t, 'denied: ' || sqlerrm); end;
end $$;
grant execute on function pg_temp.deny(text,text) to anon, authenticated;

-- ===== A1: anon =====
set role anon;
select pg_temp.deny('A1 anon admin_list_users', 'select * from public.admin_list_users()');
select pg_temp.deny('A1 anon admin_grant', 'select public.admin_grant(null, true, 1, 0, '''')');
select pg_temp.deny('A1 anon admin_message', 'select public.admin_message(null, true, ''t'', ''b'')');
select pg_temp.deny('A1 anon select admin_grants', 'select * from public.admin_grants');
select pg_temp.deny('A1 anon select admin_messages', 'select * from public.admin_messages');
select pg_temp.deny('A1 anon ack_my_grants', 'select public.ack_my_grants(''{}'')');
reset role;

-- ===== A2: normal user B (metadata claims role=admin — must not matter) =====
set role authenticated; select set_config('request.jwt.claim.sub','bbbbbbbb-0000-0000-0000-000000000002',false);
select pg_temp.deny('A2 B admin_list_users', 'select * from public.admin_list_users()');
select pg_temp.deny('A2 B admin_get_user', 'select public.admin_get_user(''aaaaaaaa-0000-0000-0000-000000000001'')');
select pg_temp.deny('A2 B admin_stats', 'select public.admin_stats()');
select pg_temp.deny('A2 B admin_audit_log', 'select * from public.admin_audit_log()');
select pg_temp.deny('A2 B admin_grant self 1e6 coins', 'select public.admin_grant(array[''bbbbbbbb-0000-0000-0000-000000000002''::uuid], false, 1000000, 0, '''')');
select pg_temp.deny('A2 B admin_grant all', 'select public.admin_grant(null, true, 5, 5, '''')');
select pg_temp.deny('A2 B admin_message all', 'select public.admin_message(null, true, ''hi'', ''spam'')');
select pg_temp.deny('A2 B admin_set_ban C', 'select public.admin_set_ban(''cccccccc-0000-0000-0000-000000000003'', true)');
select pg_temp.deny('A2 B admin_cancel_grant', 'select public.admin_cancel_grant(gen_random_uuid())');
select pg_temp.deny('A2 B codis_require_admin', 'select public.codis_require_admin()');
select pg_temp.deny('A2 B codis_admin_targets', 'select * from public.codis_admin_targets(null, true)');
select pg_temp.deny('A2 B insert admin_grants', 'insert into public.admin_grants(user_id, coins) values (''bbbbbbbb-0000-0000-0000-000000000002'', 999)');
select pg_temp.deny('A2 B insert admin_messages', 'insert into public.admin_messages(user_id, title, body) values (''cccccccc-0000-0000-0000-000000000003'', ''x'', ''y'')');
select pg_temp.deny('A2 B update admin_grants', 'update public.admin_grants set coins = 999');
select pg_temp.deny('A2 B select admin_audit', 'select * from public.admin_audit');
select pg_temp.deny('A2 B insert admins (self-promote)', 'insert into public.admins(user_id) values (''bbbbbbbb-0000-0000-0000-000000000002'')');
insert into res select 'A2 B is_admin()', public.is_admin()::text;
reset role;

-- ===== A3: admin A =====
set role authenticated; select set_config('request.jwt.claim.sub','aaaaaaaa-0000-0000-0000-000000000001',false);
insert into res select 'A3 admin list count', count(*)::text from public.admin_list_users();
insert into res select 'A3 admin list B row (photo stripped, bad json safe)', (select coalesce(profile::text,'null')||' coins='||coalesce(coins::text,'null')||' silver='||coalesce(silver::text,'null') from public.admin_list_users() where email='b@x');
insert into res select 'A3 admin list C (non-number / huge values)', (select 'coins='||coalesce(coins::text,'null')||' silver='||coalesce(silver::text,'null') from public.admin_list_users() where email='c@x');
insert into res select 'A3 admin search "Bee"', count(*)::text from public.admin_list_users('Bee');
insert into res select 'A3 admin search injection text', count(*)::text from public.admin_list_users($$%' or 1=1 --$$);
insert into res select 'A3 grant B +100 coins', public.admin_grant(array['bbbbbbbb-0000-0000-0000-000000000002'::uuid], false, 100, 0, 'gift')::text;
insert into res select 'A3 grant all +5 silver', public.admin_grant(null, true, 0, 5, 'all')::text;
insert into res select 'A3 grant unknown id (ignored)', public.admin_grant(array['dddddddd-0000-0000-0000-000000000009'::uuid], false, 1, 0, '')::text;
select pg_temp.deny('A3 grant zero', 'select public.admin_grant(null, true, 0, 0, '''')');
select pg_temp.deny('A3 grant too large', 'select public.admin_grant(null, true, 200000000, 0, '''')');
select pg_temp.deny('A3 grant no recipients', 'select public.admin_grant(''{}'', false, 1, 0, '''')');
insert into res select 'A3 message all', public.admin_message(null, true, 'Hello', 'Welcome <b>all</b>')::text;
select pg_temp.deny('A3 message empty title', 'select public.admin_message(null, true, ''  '', ''x'')');
select pg_temp.deny('A3 message 2001 chars', 'select public.admin_message(null, true, ''t'', repeat(''x'', 2001))');
insert into res select 'A3 ban C', public.admin_set_ban('cccccccc-0000-0000-0000-000000000003', true)::text;
select pg_temp.deny('A3 ban admin (self)', 'select public.admin_set_ban(''aaaaaaaa-0000-0000-0000-000000000001'', true)');
insert into res select 'A3 stats', public.admin_stats()::text;
insert into res select 'A3 audit rows', count(*)::text from public.admin_audit_log();
insert into res select 'A3 get_user B has progress', ((public.admin_get_user('bbbbbbbb-0000-0000-0000-000000000002'))->'progress'->>'version');
reset role;
insert into res select 'A3 C banned_until set (superuser view)', (banned_until > now() + interval '50 years')::text from auth.users where email='c@x';

-- ===== A4: user B reads only own gifts/messages, acks them once =====
set role authenticated; select set_config('request.jwt.claim.sub','bbbbbbbb-0000-0000-0000-000000000002',false);
insert into res select 'A4 B sees own grants', count(*)::text from public.admin_grants;
insert into res select 'A4 B sees own messages', count(*)::text from public.admin_messages;
select pg_temp.deny('A4 B read created_by column', 'select created_by from public.admin_grants');
insert into res select 'A4 B ack A''s grant ids (0)', public.ack_my_grants(array(select id from public.admin_grants where false))::text;
insert into res select 'A4 B ack own grants', public.ack_my_grants(array(select id from public.admin_grants))::text;
insert into res select 'A4 B ack again (0)', public.ack_my_grants(array(select id from public.admin_grants))::text;
insert into res select 'A4 B ack own messages', public.ack_my_messages(array(select id from public.admin_messages))::text;
reset role;
-- B tries to ack a grant that belongs to A (id taken as superuser)
select set_config('codis.a_grant', (select id::text from public.admin_grants where user_id='aaaaaaaa-0000-0000-0000-000000000001' limit 1), false);
set role authenticated; select set_config('request.jwt.claim.sub','bbbbbbbb-0000-0000-0000-000000000002',false);
insert into res select 'A4 B ack A''s grant by id (0)', public.ack_my_grants(array[current_setting('codis.a_grant')::uuid])::text;
reset role;
insert into res select 'A4 A grant still pending', (claimed_at is null)::text from public.admin_grants where id = current_setting('codis.a_grant')::uuid;

-- ===== A5: hardening =====
insert into res select 'A5 secdef + search_path '||p.proname, 'secdef='||p.prosecdef||' cfg='||coalesce(array_to_string(p.proconfig,','),'NONE')
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and (p.proname like 'admin_%' or p.proname like 'ack_my_%' or p.proname like 'codis_%') order by p.proname;
insert into res select 'A5 RLS '||c.relname, c.relrowsecurity::text from pg_class c join pg_namespace n on n.oid=c.relnamespace
 where n.nspname='public' and c.relname in ('admin_grants','admin_messages','admin_audit') order by c.relname;
insert into res select 'A5 anon/authenticated EXECUTE on internal helpers', coalesce(string_agg(p.proname||':'||r.rolname, ','), 'none')
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace cross join (values ('anon'),('authenticated')) r(rolname)
 where n.nspname='public' and p.proname in ('codis_require_admin','codis_admin_targets','codis_json_int') and has_function_privilege(r.rolname, p.oid, 'execute');

select t||'|'||r from res;
