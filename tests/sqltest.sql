\set ON_ERROR_STOP off
\pset pager off
create temp table res(t text, r text);
grant all on res to anon, authenticated;
-- users
insert into auth.users(id,email) values
 ('aaaaaaaa-0000-0000-0000-000000000001','a@x'),('bbbbbbbb-0000-0000-0000-000000000002','b@x');

create or replace function pg_temp.as_user(u text) returns void language plpgsql as $$
begin perform set_config('request.jwt.claim.sub', u, false); end $$;

-- T1 anon
set role anon;
do $$ begin begin perform * from public.progress; insert into res values('T1 anon select progress','UNEXPECTED ok'); exception when others then insert into res values('T1 anon select progress','denied: '||sqlerrm); end; end $$;
do $$ begin begin perform public.save_progress('{}'::jsonb,0); insert into res values('T1 anon save_progress','UNEXPECTED ok'); exception when others then insert into res values('T1 anon save_progress','denied: '||sqlerrm); end; end $$;
do $$ begin begin perform public.delete_my_account(); insert into res values('T1 anon delete_my_account','UNEXPECTED ok'); exception when others then insert into res values('T1 anon delete_my_account','denied: '||sqlerrm); end; end $$;
do $$ begin begin perform * from public.admins; insert into res values('T1 anon select admins','UNEXPECTED ok'); exception when others then insert into res values('T1 anon select admins','denied: '||sqlerrm); end; end $$;
reset role;

-- T2 user A sequence
set role authenticated; select set_config('request.jwt.claim.sub','aaaaaaaa-0000-0000-0000-000000000001',false);
insert into res select 'T2 A first save base0', public.save_progress('{"x":1}',0)::text;
insert into res select 'T2 A save base0 again (conflict)', public.save_progress('{"x":2}',0)::text;
insert into res select 'T2 A save base1 -> v2', public.save_progress('{"x":3}',1)::text;
insert into res select 'T2 A save stale base1 (conflict v2)', public.save_progress('{"x":9}',1)::text;
insert into res select 'T2 A save base99 (conflict)', public.save_progress('{"x":9}',99)::text;
insert into res select 'T2 A read own row', (select data::text||' v'||version from public.progress);
do $$ begin begin perform public.save_progress('[1,2]'::jsonb,2); insert into res values('T5 array payload','UNEXPECTED ok'); exception when others then insert into res values('T5 array payload','rejected: '||sqlerrm); end; end $$;
do $$ begin begin perform public.save_progress(null,2); insert into res values('T5 null payload','UNEXPECTED ok'); exception when others then insert into res values('T5 null payload','rejected: '||sqlerrm); end; end $$;
do $$ begin begin perform public.save_progress(jsonb_build_object('big', repeat('x',9000000)),2); insert into res values('T5 9MB payload','UNEXPECTED ok'); exception when others then insert into res values('T5 9MB payload','rejected: '||sqlerrm); end; end $$;
reset role;

-- T3 user B isolation
set role authenticated; select set_config('request.jwt.claim.sub','bbbbbbbb-0000-0000-0000-000000000002',false);
insert into res select 'T3 B sees A rows? (count)', count(*)::text from public.progress;
do $$ begin begin update public.progress set data='{"hack":1}'; insert into res values('T3 B direct UPDATE','UNEXPECTED ok (rows: '||(select count(*) from public.progress)||')'); exception when others then insert into res values('T3 B direct UPDATE','denied: '||sqlerrm); end; end $$;
do $$ begin begin insert into public.progress(user_id,data) values('aaaaaaaa-0000-0000-0000-000000000001','{}'); insert into res values('T3 B direct INSERT as A','UNEXPECTED ok'); exception when others then insert into res values('T3 B direct INSERT as A','denied: '||sqlerrm); end; end $$;
do $$ begin begin delete from public.progress; insert into res values('T3 B direct DELETE','UNEXPECTED ok'); exception when others then insert into res values('T3 B direct DELETE','denied: '||sqlerrm); end; end $$;
insert into res select 'T4 B no row, base5 -> conflict null', public.save_progress('{"b":1}',5)::text;
insert into res select 'T4 B first save base0', public.save_progress('{"b":1}',0)::text;
-- B cannot target A's row via RPC (owner derived from JWT)
insert into res select 'T3 B RPC only touches B (B version)', (select version::text from public.progress);
reset role;
insert into res select 'T3 A row untouched (superuser view)', data::text||' v'||version from public.progress where user_id='aaaaaaaa-0000-0000-0000-000000000001';

-- T6 admin + storage
insert into storage.objects(bucket_id,name) values('dev-addon','dev-addon.js'),('other','x.txt');
set role authenticated; select set_config('request.jwt.claim.sub','bbbbbbbb-0000-0000-0000-000000000002',false);
insert into res select 'T6 non-admin is_admin()', public.is_admin()::text;
insert into res select 'T6 non-admin admins rows', count(*)::text from public.admins;
insert into res select 'T6 non-admin storage rows', count(*)::text from storage.objects;
do $$ begin begin insert into public.admins(user_id) values('bbbbbbbb-0000-0000-0000-000000000002'); insert into res values('T6 self-promote INSERT admins','UNEXPECTED ok'); exception when others then insert into res values('T6 self-promote INSERT admins','denied: '||sqlerrm); end; end $$;
reset role;
insert into public.admins(user_id) values('aaaaaaaa-0000-0000-0000-000000000001');
set role authenticated; select set_config('request.jwt.claim.sub','aaaaaaaa-0000-0000-0000-000000000001',false);
insert into res select 'T6 admin is_admin()', public.is_admin()::text;
insert into res select 'T6 admin sees own admin rows', count(*)::text from public.admins;
insert into res select 'T6 admin storage rows (dev-addon only)', string_agg(bucket_id||'/'||name, ',') from storage.objects;
reset role;
set role authenticated; select set_config('request.jwt.claim.sub','bbbbbbbb-0000-0000-0000-000000000002',false);
insert into res select 'T6 B still blocked from storage', count(*)::text from storage.objects;
reset role;

-- T7 delete account
set role authenticated; select set_config('request.jwt.claim.sub','aaaaaaaa-0000-0000-0000-000000000001',false);
select public.delete_my_account();
reset role;
insert into res select 'T7 A progress rows after delete', count(*)::text from public.progress where user_id='aaaaaaaa-0000-0000-0000-000000000001';
insert into res select 'T7 A auth.users rows after delete', count(*)::text from auth.users where id='aaaaaaaa-0000-0000-0000-000000000001';
insert into res select 'T7 A admins rows after delete (cascade)', count(*)::text from public.admins where user_id='aaaaaaaa-0000-0000-0000-000000000001';
insert into res select 'T7 B untouched', count(*)::text from public.progress where user_id='bbbbbbbb-0000-0000-0000-000000000002';
-- deleted user's still-valid JWT cannot recreate data (FK)
set role authenticated; select set_config('request.jwt.claim.sub','aaaaaaaa-0000-0000-0000-000000000001',false);
do $$ begin begin perform public.save_progress('{"z":1}',0); insert into res values('T7 stale JWT save after delete','UNEXPECTED ok'); exception when others then insert into res values('T7 stale JWT save after delete','rejected: '||sqlerrm); end; end $$;
reset role;

-- T8 config of functions
insert into res select 'T8 search_path pinned: '||p.proname, coalesce(array_to_string(p.proconfig,','),'NONE')||' secdef='||p.prosecdef
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' order by p.proname;
insert into res select 'T8 RLS enabled '||c.relname, c.relrowsecurity::text from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname in ('progress','admins');
select t, r from res order by ctid;
