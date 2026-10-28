-- =====================================================================
-- CODIS — Supabase setup (idempotent: safe to run more than once)
-- Run in: Supabase Dashboard → SQL Editor (as the default `postgres` role).
--
-- Derived from what the app code actually calls (CODIS_9-7-2.html):
--   GET  /rest/v1/progress?select=data,version,updated_at&user_id=eq.<uid>
--   POST /rest/v1/rpc/save_progress   { p_data jsonb, p_base_version bigint }
--   POST /rest/v1/rpc/delete_my_account   {}
--   GET  /rest/v1/admins?select=user_id
--   GET  /storage/v1/object/authenticated/dev-addon/dev-addon.js
--
-- Security model: the browser only ever holds the anon/publishable key + the
-- user's own JWT. Every write goes through SECURITY DEFINER RPCs that derive
-- the owner from auth.uid() (never from a client-supplied id). Direct
-- INSERT/UPDATE/DELETE on the tables is not granted to anyone.
-- NOTHING here disables RLS or grants broad access.
-- =====================================================================

-- ---------- 1) progress: one snapshot row per user ----------
create table if not exists public.progress (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  data       jsonb       not null,
  version    bigint      not null default 1,
  updated_at timestamptz not null default now()
);

alter table public.progress enable row level security;

drop policy if exists progress_select_own on public.progress;
create policy progress_select_own on public.progress
  for select to authenticated
  using ((select auth.uid()) = user_id);

revoke all on public.progress from public, anon, authenticated;
grant select on public.progress to authenticated;     -- read own row only (RLS)

-- ---------- 2) admins: who may load the private developer add-on ----------
create table if not exists public.admins (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);

alter table public.admins enable row level security;

drop policy if exists admins_select_self on public.admins;
create policy admins_select_self on public.admins
  for select to authenticated
  using ((select auth.uid()) = user_id);              -- a user can only see *their own* admin row

revoke all on public.admins from public, anon, authenticated;
grant select on public.admins to authenticated;
-- Admins are added ONLY by the project owner, e.g. (SQL editor):
--   insert into public.admins(user_id) select id from auth.users where email = 'you@example.com';

-- ---------- 3) helper: trusted server-side admin check ----------
create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (select 1 from public.admins a where a.user_id = (select auth.uid()));
$$;
revoke all on function public.is_admin() from public, anon;
grant execute on function public.is_admin() to authenticated;

-- ---------- 4) save_progress: optimistic-concurrency snapshot save ----------
-- Contract expected by the client:
--   ok       -> { "ok": true, "version": <new version> }
--   conflict -> { "ok": false, "conflict": true, "version": <server version>,
--                 "data": <server snapshot | null>, "updated_at": <ts> }
--   (no server row but client base <> 0 -> conflict with data = null, version = 0;
--    the client then re-bases to 0 and retries)
create or replace function public.save_progress(p_data jsonb, p_base_version bigint)
returns jsonb
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_uid  uuid   := auth.uid();
  v_base bigint := coalesce(p_base_version, 0);
  v_row  public.progress%rowtype;
  v_new  bigint;
begin
  if v_uid is null then
    raise exception 'not authenticated' using errcode = '28000';
  end if;
  if p_data is null or jsonb_typeof(p_data) <> 'object' then
    raise exception 'p_data must be a JSON object' using errcode = '22023';
  end if;
  if octet_length(p_data::text) > 8388608 then
    raise exception 'payload too large (max 8 MB)' using errcode = '54000';
  end if;

  select * into v_row from public.progress where user_id = v_uid for update;

  if not found then
    if v_base <> 0 then
      return jsonb_build_object('ok', false, 'conflict', true, 'version', 0, 'data', null);
    end if;
    insert into public.progress(user_id, data, version, updated_at)
    values (v_uid, p_data, 1, now())
    on conflict (user_id) do nothing;
    if found then
      return jsonb_build_object('ok', true, 'version', 1);
    end if;
    -- lost a race with a concurrent first save
    select * into v_row from public.progress where user_id = v_uid;
    return jsonb_build_object('ok', false, 'conflict', true, 'version', v_row.version,
                              'data', v_row.data, 'updated_at', v_row.updated_at);
  end if;

  if v_row.version = v_base then
    update public.progress
       set data = p_data, version = v_row.version + 1, updated_at = now()
     where user_id = v_uid
    returning version into v_new;
    return jsonb_build_object('ok', true, 'version', v_new);
  end if;

  return jsonb_build_object('ok', false, 'conflict', true, 'version', v_row.version,
                            'data', v_row.data, 'updated_at', v_row.updated_at);
end;
$$;
revoke all on function public.save_progress(jsonb, bigint) from public, anon;
grant execute on function public.save_progress(jsonb, bigint) to authenticated;

-- ---------- 5) delete_my_account: removes data AND the auth identity ----------
-- Raises on failure, so the client never reports a deletion that did not happen.
create or replace function public.delete_my_account()
returns void
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
begin
  if v_uid is null then
    raise exception 'not authenticated' using errcode = '28000';
  end if;
  delete from public.progress where user_id = v_uid;
  delete from auth.users where id = v_uid;          -- cascades to admins / sessions / identities
end;
$$;
revoke all on function public.delete_my_account() from public, anon;
grant execute on function public.delete_my_account() to authenticated;

-- ---------- 6) private storage bucket for the developer add-on ----------
insert into storage.buckets (id, name, public)
values ('dev-addon', 'dev-addon', false)
on conflict (id) do update set public = false;

drop policy if exists dev_addon_admin_read on storage.objects;
create policy dev_addon_admin_read on storage.objects
  for select to authenticated
  using (bucket_id = 'dev-addon' and public.is_admin());
-- No INSERT/UPDATE/DELETE policy on purpose: upload dev-addon.js from the
-- Dashboard (Storage → dev-addon) which uses privileged access.

-- ---------- 7) make PostgREST pick up the new functions/tables immediately ----------
notify pgrst, 'reload schema';
