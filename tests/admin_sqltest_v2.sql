\set ON_ERROR_STOP off
\pset pager off
-- CODIS-HUB admin v2 tests (run after stub.sql + codis_supabase_setup.sql + codis_admin.sql + codis_admin_v2.sql)
create temp table res(t text, r text);
grant all on res to anon, authenticated;
insert into auth.users(id,email,raw_user_meta_data,created_at,last_sign_in_at) values
 ('aaaaaaaa-0000-0000-0000-000000000001','admin@x','{"full_name":"Admin"}',now(),now()),
 ('bbbbbbbb-0000-0000-0000-000000000002','b@x','{"full_name":"Bee"}',now(),now()),
 ('cccccccc-0000-0000-0000-000000000003','c@x','{}',now(),null);
insert into public.admins(user_id) values ('aaaaaaaa-0000-0000-0000-000000000001');
create or replace function pg_temp.deny(t text, q text) returns void language plpgsql as $$
begin
  begin execute q; insert into res values(t, 'UNEXPECTED ok');
  exception when others then insert into res values(t, 'denied: ' || sqlerrm); end;
end $$;
grant execute on function pg_temp.deny(text,text) to anon, authenticated;

-- B1 anon
set role anon;
select pg_temp.deny('B1 anon admin_grant_v2', 'select public.admin_grant_v2(null, true, 1, 0, '''', gen_random_uuid())');
select pg_temp.deny('B1 anon admin_message_v2', 'select public.admin_message_v2(null, true, ''t'', ''b'', gen_random_uuid())');
select pg_temp.deny('B1 anon admin_list_grants', 'select * from public.admin_list_grants()');
select pg_temp.deny('B1 anon admin_list_messages', 'select * from public.admin_list_messages()');
reset role;

-- B2 normal user B
set role authenticated; select set_config('request.jwt.claim.sub','bbbbbbbb-0000-0000-0000-000000000002',false);
select pg_temp.deny('B2 B admin_grant_v2 self', 'select public.admin_grant_v2(array[''bbbbbbbb-0000-0000-0000-000000000002''::uuid], false, 999999, 0, '''', gen_random_uuid())');
select pg_temp.deny('B2 B admin_message_v2', 'select public.admin_message_v2(null, true, ''t'', ''b'', gen_random_uuid())');
select pg_temp.deny('B2 B admin_list_grants', 'select * from public.admin_list_grants()');
select pg_temp.deny('B2 B admin_list_messages', 'select * from public.admin_list_messages()');
reset role;

-- B3 admin A
set role authenticated; select set_config('request.jwt.claim.sub','aaaaaaaa-0000-0000-0000-000000000001',false);
insert into res select 'B3 first send creates 3 rows, not duplicate', (public.admin_grant_v2(null, true, 50, 0, 'hi', '11111111-1111-4111-8111-111111111111') - 'request')::text;
insert into res select 'B3 retry SAME request: duplicate=true, nothing new', (public.admin_grant_v2(null, true, 50, 0, 'hi', '11111111-1111-4111-8111-111111111111') - 'request')::text;
insert into res select 'B3 rows after retry (must be 3: A,B,C)', count(*)::text from public.admin_list_grants();
insert into res select 'B3 audit rows for the grant (must be 1)', count(*)::text from public.admin_audit_log() where action = 'grant';
insert into res select 'B3 NEW request creates new row', (public.admin_grant_v2(array['bbbbbbbb-0000-0000-0000-000000000002'::uuid], false, -5, 3, 'adj', '22222222-2222-4222-8222-222222222222') - 'request')::text;
select pg_temp.deny('B3 null request refused', 'select public.admin_grant_v2(null, true, 1, 0, '''', null)');
select pg_temp.deny('B3 nothing to grant refused', 'select public.admin_grant_v2(null, true, 0, 0, '''', gen_random_uuid())');
select pg_temp.deny('B3 too large refused', 'select public.admin_grant_v2(null, true, 100000001, 0, '''', gen_random_uuid())');
insert into res select 'B3 list pending (must be 4)', count(*)::text from public.admin_list_grants('pending');
insert into res select 'B3 list search adj (must be 1)', count(*)::text from public.admin_list_grants('', 'adj');
insert into res select 'B3 message v2 first', (public.admin_message_v2(array['bbbbbbbb-0000-0000-0000-000000000002'::uuid], false, 'T', 'Body', '33333333-3333-4333-8333-333333333333') - 'request')::text;
insert into res select 'B3 message v2 retry duplicate', (public.admin_message_v2(array['bbbbbbbb-0000-0000-0000-000000000002'::uuid], false, 'T', 'Body', '33333333-3333-4333-8333-333333333333') - 'request')::text;
insert into res select 'B3 messages rows (must be 1)', count(*)::text from public.admin_list_messages();
reset role;

-- B4 user B: applies own gifts, cannot read request_id / created_by
set role authenticated; select set_config('request.jwt.claim.sub','bbbbbbbb-0000-0000-0000-000000000002',false);
select pg_temp.deny('B4 B cannot read request_id', 'select request_id from public.admin_grants');
select pg_temp.deny('B4 B cannot read created_by', 'select created_by from public.admin_grants');
insert into res select 'B4 B sees only own rows (must be 2)', count(*)::text from public.admin_grants;
insert into res select 'B4 B acks own gifts (must be 2)', public.ack_my_grants(array(select id from public.admin_grants))::text;
reset role;

-- B5 admin A: statuses
set role authenticated; select set_config('request.jwt.claim.sub','aaaaaaaa-0000-0000-0000-000000000001',false);
insert into res select 'B5 applied (must be 2)', count(*)::text from public.admin_list_grants('applied');
insert into res select 'B5 pending before cancel (must be 2: A,C)', count(*)::text from public.admin_list_grants('pending');
insert into res select 'B5 cancel one pending', public.admin_cancel_grant((select id from public.admin_list_grants('pending') limit 1))::text;
insert into res select 'B5 cancelled (must be 1)', count(*)::text from public.admin_list_grants('cancelled');
insert into res select 'B5 pending after cancel (must be 1)', count(*)::text from public.admin_list_grants('pending');
reset role;

select t||'|'||r from res;
