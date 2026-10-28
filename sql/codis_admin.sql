-- =====================================================================
-- CODIS — Developer (admin) powers. Idempotent: safe to run more than once.
-- Run AFTER codis_supabase_setup.sql, in: Supabase Dashboard → SQL Editor.
--
-- Security model (same as the base file):
--   * Who is an admin is decided ONLY by a row in public.admins, which only the
--     project owner can insert (SQL editor). Nothing here lets anyone add admins.
--   * Every admin power is a SECURITY DEFINER function that first calls
--     public.codis_require_admin(): it reads auth.uid() from the caller's JWT
--     (never from a parameter) and raises 42501 for anyone not in public.admins.
--     Knowing the function names or having the add-on code gives no power.
--   * Normal users can only READ their own gifts/messages (RLS + column grants)
--     and mark their own rows as received. No direct INSERT/UPDATE/DELETE.
--   * user_metadata is never used for authorization (users can edit it).
--   * NOTHING here disables RLS or grants broad access.
-- =====================================================================

-- ---------- 1) tables ----------
create table if not exists public.admin_grants (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  coins       bigint not null default 0,
  silver      bigint not null default 0,
  note        text   not null default '',
  created_by  uuid,
  created_at  timestamptz not null default now(),
  claimed_at  timestamptz,
  cancelled_at timestamptz,
  constraint admin_grants_amounts check (abs(coins) <= 100000000 and abs(silver) <= 100000000 and (coins <> 0 or silver <> 0)),
  constraint admin_grants_note check (char_length(note) <= 200)
);
create index if not exists admin_grants_pending on public.admin_grants(user_id) where claimed_at is null and cancelled_at is null;

create table if not exists public.admin_messages (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references auth.users(id) on delete cascade,
  title        text not null,
  body         text not null,
  created_by   uuid,
  created_at   timestamptz not null default now(),
  delivered_at timestamptz,
  constraint admin_messages_title check (char_length(title) between 1 and 120),
  constraint admin_messages_body  check (char_length(body) between 1 and 2000)
);
create index if not exists admin_messages_pending on public.admin_messages(user_id) where delivered_at is null;

create table if not exists public.admin_audit (
  id         bigserial primary key,
  admin_id   uuid not null,
  action     text not null,
  targets    int  not null default 0,
  detail     jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.admin_grants   enable row level security;
alter table public.admin_messages enable row level security;
alter table public.admin_audit    enable row level security;

revoke all on public.admin_grants, public.admin_messages, public.admin_audit from public, anon, authenticated;
revoke all on sequence public.admin_audit_id_seq from public, anon, authenticated;

-- a user reads ONLY their own rows, and only these columns (created_by — the admin's id — is not exposed)
drop policy if exists admin_grants_select_own on public.admin_grants;
create policy admin_grants_select_own on public.admin_grants
  for select to authenticated using ((select auth.uid()) = user_id);
grant select (id, user_id, coins, silver, note, created_at, claimed_at, cancelled_at) on public.admin_grants to authenticated;

drop policy if exists admin_messages_select_own on public.admin_messages;
create policy admin_messages_select_own on public.admin_messages
  for select to authenticated using ((select auth.uid()) = user_id);
grant select (id, user_id, title, body, created_at, delivered_at) on public.admin_messages to authenticated;
-- admin_audit: no policy and no grant → only reachable through admin functions.

-- ---------- 2) the one gate every admin function goes through ----------
create or replace function public.codis_require_admin()
returns uuid
language plpgsql
stable
security definer
set search_path = ''
as $$
declare v uuid := auth.uid();
begin
  if v is null or not exists (select 1 from public.admins a where a.user_id = v) then
    raise exception 'admin only' using errcode = '42501';
  end if;
  return v;
end;
$$;
revoke all on function public.codis_require_admin() from public, anon, authenticated;   -- internal helper only

-- resolve targets: explicit ids that really exist, or every user (p_all). Max 10000 per call.
create or replace function public.codis_admin_targets(p_user_ids uuid[], p_all boolean)
returns setof uuid
language plpgsql
stable
security definer
set search_path = ''
as $$
begin
  if coalesce(p_all, false) then
    return query select u.id from auth.users u;
  else
    if p_user_ids is null or cardinality(p_user_ids) = 0 then
      raise exception 'no recipients' using errcode = '22023';
    end if;
    if cardinality(p_user_ids) > 10000 then
      raise exception 'too many recipients' using errcode = '22023';
    end if;
    return query select distinct u.id from auth.users u where u.id = any(p_user_ids);
  end if;
end;
$$;
revoke all on function public.codis_admin_targets(uuid[], boolean) from public, anon, authenticated;

-- numeric value from user-controlled JSON without ever raising
create or replace function public.codis_json_int(j jsonb)
returns bigint
language sql
immutable
set search_path = ''
as $$
  select case when jsonb_typeof(j) = 'number'
              then trunc(greatest(least((j #>> '{}')::numeric, 9e15), -9e15))::bigint
              else null end;
$$;
revoke all on function public.codis_json_int(jsonb) from public, anon, authenticated;

-- ---------- 3) admin: read ----------
drop function if exists public.admin_list_users(text, int, int);
create or replace function public.admin_list_users(p_search text default '', p_limit int default 500, p_offset int default 0)
returns table (
  user_id uuid, email text, full_name text, avatar_url text, created_at timestamptz, last_sign_in_at timestamptz,
  banned boolean, is_admin boolean, profile jsonb, coins bigint, silver bigint,
  progress_version bigint, progress_updated_at timestamptz, pending_grants int, pending_messages int, total_count bigint
)
language plpgsql
stable
security definer
set search_path = ''
as $$
declare s text := '%' || coalesce(trim(p_search), '') || '%';
begin
  perform public.codis_require_admin();
  return query
  select u.id, u.email::text,
         coalesce(u.raw_user_meta_data->>'full_name', u.raw_user_meta_data->>'name'),
         u.raw_user_meta_data->>'avatar_url',
         u.created_at, u.last_sign_in_at,
         coalesce(u.banned_until > now(), false),
         exists (select 1 from public.admins a where a.user_id = u.id),
         case when jsonb_typeof(p.data->'profile') = 'object' then (p.data->'profile') - 'photo' else null end,
         public.codis_json_int(p.data->'wallet'->'balance'),
         public.codis_json_int(p.data->'wallet'->'silver'->'balance'),
         p.version, p.updated_at,
         (select count(*)::int from public.admin_grants g where g.user_id = u.id and g.claimed_at is null and g.cancelled_at is null),
         (select count(*)::int from public.admin_messages m where m.user_id = u.id and m.delivered_at is null),
         count(*) over ()
    from auth.users u
    left join public.progress p on p.user_id = u.id
   where coalesce(trim(p_search), '') = ''
      or u.email ilike s
      or coalesce(u.raw_user_meta_data->>'full_name', u.raw_user_meta_data->>'name', '') ilike s
      or coalesce(p.data->'profile'->>'name', '') ilike s
   order by u.last_sign_in_at desc nulls last, u.created_at desc
   limit greatest(1, least(coalesce(p_limit, 500), 1000)) offset greatest(0, coalesce(p_offset, 0));
end;
$$;
revoke all on function public.admin_list_users(text, int, int) from public, anon;
grant execute on function public.admin_list_users(text, int, int) to authenticated;

create or replace function public.admin_get_user(p_user uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare r jsonb;
begin
  perform public.codis_require_admin();
  select jsonb_build_object(
    'user', jsonb_build_object('id', u.id, 'email', u.email, 'created_at', u.created_at, 'last_sign_in_at', u.last_sign_in_at,
                               'banned', coalesce(u.banned_until > now(), false),
                               'is_admin', exists (select 1 from public.admins a where a.user_id = u.id),
                               'full_name', coalesce(u.raw_user_meta_data->>'full_name', u.raw_user_meta_data->>'name'),
                               'avatar_url', u.raw_user_meta_data->>'avatar_url'),
    'progress', (select jsonb_build_object('version', p.version, 'updated_at', p.updated_at, 'data', p.data) from public.progress p where p.user_id = u.id),
    'grants', coalesce((select jsonb_agg(to_jsonb(g) order by g.created_at desc) from (select id, coins, silver, note, created_at, claimed_at, cancelled_at from public.admin_grants where user_id = u.id order by created_at desc limit 100) g), '[]'::jsonb),
    'messages', coalesce((select jsonb_agg(to_jsonb(m) order by m.created_at desc) from (select id, title, body, created_at, delivered_at from public.admin_messages where user_id = u.id order by created_at desc limit 100) m), '[]'::jsonb))
  into r
  from auth.users u where u.id = p_user;
  if r is null then raise exception 'user not found' using errcode = 'P0002'; end if;
  return r;
end;
$$;
revoke all on function public.admin_get_user(uuid) from public, anon;
grant execute on function public.admin_get_user(uuid) to authenticated;

create or replace function public.admin_stats()
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
begin
  perform public.codis_require_admin();
  return jsonb_build_object(
    'users',            (select count(*) from auth.users),
    'active_7d',        (select count(*) from auth.users where last_sign_in_at > now() - interval '7 days'),
    'active_30d',       (select count(*) from auth.users where last_sign_in_at > now() - interval '30 days'),
    'with_progress',    (select count(*) from public.progress),
    'banned',           (select count(*) from auth.users where banned_until > now()),
    'coins_total',      (select coalesce(sum(public.codis_json_int(data->'wallet'->'balance')), 0) from public.progress),
    'silver_total',     (select coalesce(sum(public.codis_json_int(data->'wallet'->'silver'->'balance')), 0) from public.progress),
    'pending_grants',   (select count(*) from public.admin_grants where claimed_at is null and cancelled_at is null),
    'pending_messages', (select count(*) from public.admin_messages where delivered_at is null),
    'admins',           (select count(*) from public.admins));
end;
$$;
revoke all on function public.admin_stats() from public, anon;
grant execute on function public.admin_stats() to authenticated;

drop function if exists public.admin_audit_log(int);
create or replace function public.admin_audit_log(p_limit int default 100)
returns table (id bigint, admin_email text, action text, targets int, detail jsonb, created_at timestamptz)
language plpgsql
stable
security definer
set search_path = ''
as $$
begin
  perform public.codis_require_admin();
  return query
  select a.id, u.email::text, a.action, a.targets, a.detail, a.created_at
    from public.admin_audit a left join auth.users u on u.id = a.admin_id
   order by a.id desc
   limit greatest(1, least(coalesce(p_limit, 100), 1000));
end;
$$;
revoke all on function public.admin_audit_log(int) from public, anon;
grant execute on function public.admin_audit_log(int) to authenticated;

-- ---------- 4) admin: actions (each one is written to admin_audit) ----------
-- coins/silver gift (negative = deduct; the app never lets a balance go below zero)
create or replace function public.admin_grant(p_user_ids uuid[], p_all boolean, p_coins bigint, p_silver bigint, p_note text default '')
returns int
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare v_admin uuid := public.codis_require_admin(); n int;
begin
  p_coins := coalesce(p_coins, 0); p_silver := coalesce(p_silver, 0); p_note := left(coalesce(trim(p_note), ''), 200);
  if p_coins = 0 and p_silver = 0 then raise exception 'nothing to grant' using errcode = '22023'; end if;
  if abs(p_coins) > 100000000 or abs(p_silver) > 100000000 then raise exception 'amount too large' using errcode = '22023'; end if;
  insert into public.admin_grants(user_id, coins, silver, note, created_by)
  select t, p_coins, p_silver, p_note, v_admin from public.codis_admin_targets(p_user_ids, p_all) t;
  get diagnostics n = row_count;
  insert into public.admin_audit(admin_id, action, targets, detail)
  values (v_admin, 'grant', n, jsonb_build_object('coins', p_coins, 'silver', p_silver, 'note', p_note, 'all', coalesce(p_all, false)));
  return n;
end;
$$;
revoke all on function public.admin_grant(uuid[], boolean, bigint, bigint, text) from public, anon;
grant execute on function public.admin_grant(uuid[], boolean, bigint, bigint, text) to authenticated;

create or replace function public.admin_cancel_grant(p_id uuid)
returns boolean
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare v_admin uuid := public.codis_require_admin(); n int;
begin
  update public.admin_grants set cancelled_at = now() where id = p_id and claimed_at is null and cancelled_at is null;
  get diagnostics n = row_count;
  if n > 0 then insert into public.admin_audit(admin_id, action, targets, detail) values (v_admin, 'cancel_grant', 1, jsonb_build_object('grant', p_id)); end if;
  return n > 0;
end;
$$;
revoke all on function public.admin_cancel_grant(uuid) from public, anon;
grant execute on function public.admin_cancel_grant(uuid) to authenticated;

create or replace function public.admin_message(p_user_ids uuid[], p_all boolean, p_title text, p_body text)
returns int
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare v_admin uuid := public.codis_require_admin(); n int;
begin
  p_title := trim(coalesce(p_title, '')); p_body := trim(coalesce(p_body, ''));
  if char_length(p_title) not between 1 and 120 then raise exception 'title must be 1-120 characters' using errcode = '22023'; end if;
  if char_length(p_body) not between 1 and 2000 then raise exception 'message must be 1-2000 characters' using errcode = '22023'; end if;
  insert into public.admin_messages(user_id, title, body, created_by)
  select t, p_title, p_body, v_admin from public.codis_admin_targets(p_user_ids, p_all) t;
  get diagnostics n = row_count;
  insert into public.admin_audit(admin_id, action, targets, detail)
  values (v_admin, 'message', n, jsonb_build_object('title', p_title, 'all', coalesce(p_all, false)));
  return n;
end;
$$;
revoke all on function public.admin_message(uuid[], boolean, text, text) from public, anon;
grant execute on function public.admin_message(uuid[], boolean, text, text) to authenticated;

-- block / unblock sign-in. Admin accounts cannot be blocked (no lock-out of the owner).
create or replace function public.admin_set_ban(p_user uuid, p_banned boolean)
returns boolean
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare v_admin uuid := public.codis_require_admin(); n int;
begin
  if exists (select 1 from public.admins a where a.user_id = p_user) then
    raise exception 'cannot ban an admin' using errcode = '42501';
  end if;
  update auth.users set banned_until = case when coalesce(p_banned, false) then now() + interval '100 years' else null end where id = p_user;
  get diagnostics n = row_count;
  if n > 0 then insert into public.admin_audit(admin_id, action, targets, detail) values (v_admin, case when p_banned then 'ban' else 'unban' end, 1, jsonb_build_object('user', p_user)); end if;
  return n > 0;
end;
$$;
revoke all on function public.admin_set_ban(uuid, boolean) from public, anon;
grant execute on function public.admin_set_ban(uuid, boolean) to authenticated;

-- ---------- 5) normal user: mark own gifts/messages as received ----------
create or replace function public.ack_my_grants(p_ids uuid[])
returns int
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare v uuid := auth.uid(); n int;
begin
  if v is null then raise exception 'not authenticated' using errcode = '28000'; end if;
  update public.admin_grants set claimed_at = now()
   where user_id = v and id = any(coalesce(p_ids, '{}')) and claimed_at is null and cancelled_at is null;
  get diagnostics n = row_count; return n;
end;
$$;
revoke all on function public.ack_my_grants(uuid[]) from public, anon;
grant execute on function public.ack_my_grants(uuid[]) to authenticated;

create or replace function public.ack_my_messages(p_ids uuid[])
returns int
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare v uuid := auth.uid(); n int;
begin
  if v is null then raise exception 'not authenticated' using errcode = '28000'; end if;
  update public.admin_messages set delivered_at = now()
   where user_id = v and id = any(coalesce(p_ids, '{}')) and delivered_at is null;
  get diagnostics n = row_count; return n;
end;
$$;
revoke all on function public.ack_my_messages(uuid[]) from public, anon;
grant execute on function public.ack_my_messages(uuid[]) to authenticated;

notify pgrst, 'reload schema';
