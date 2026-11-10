-- =====================================================================
-- CODIS — Developer (admin) powers, v2 (CODIS-HUB 3.26.0). Idempotent: safe to run more than once.
-- Run AFTER codis_supabase_setup.sql and codis_admin.sql, in: Supabase Dashboard → SQL Editor.
-- NOT applied to production by the assistant: apply it yourself (or approve it explicitly) — the Developer Hub works without it
-- (it falls back to admin_grant/admin_message and marks interrupted sends «unconfirmed» instead of retrying).
--
-- What it adds (nothing here weakens v1):
--   1) request ids: admin_grant_v2 / admin_message_v2 take a client-generated UUID. Re-sending the SAME request (network retry)
--      returns {duplicate:true} and creates NOTHING new — the gift/message can never be created twice.
--   2) admin_list_grants / admin_list_messages: log with real status (pending · applied · cancelled / pending · delivered), search and paging.
-- Security model is unchanged: every function starts with public.codis_require_admin() (auth.uid() from the JWT, row in public.admins);
-- normal users cannot call anything here; the new column request_id is NOT in the users' column grant, so users cannot read it.
-- =====================================================================

alter table public.admin_grants   add column if not exists request_id uuid;
alter table public.admin_messages add column if not exists request_id uuid;
create unique index if not exists admin_grants_request_uq   on public.admin_grants(created_by, request_id, user_id)   where request_id is not null;
create unique index if not exists admin_messages_request_uq on public.admin_messages(created_by, request_id, user_id) where request_id is not null;

create or replace function public.admin_grant_v2(p_user_ids uuid[], p_all boolean, p_coins bigint, p_silver bigint, p_note text, p_request uuid)
returns jsonb
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare v_admin uuid := public.codis_require_admin(); fresh int; n int;
begin
  if p_request is null then raise exception 'request id required' using errcode = '22023'; end if;
  p_coins := coalesce(p_coins, 0); p_silver := coalesce(p_silver, 0); p_note := left(coalesce(trim(p_note), ''), 200);
  if p_coins = 0 and p_silver = 0 then raise exception 'nothing to grant' using errcode = '22023'; end if;
  if abs(p_coins) > 100000000 or abs(p_silver) > 100000000 then raise exception 'amount too large' using errcode = '22023'; end if;
  insert into public.admin_grants(user_id, coins, silver, note, created_by, request_id)
  select t, p_coins, p_silver, p_note, v_admin, p_request from public.codis_admin_targets(p_user_ids, p_all) t
  on conflict (created_by, request_id, user_id) where request_id is not null do nothing;
  get diagnostics fresh = row_count;
  select count(*)::int into n from public.admin_grants g where g.created_by = v_admin and g.request_id = p_request;
  if fresh > 0 then
    insert into public.admin_audit(admin_id, action, targets, detail)
    values (v_admin, 'grant', fresh, jsonb_build_object('coins', p_coins, 'silver', p_silver, 'note', p_note, 'all', coalesce(p_all, false), 'request', p_request));
  end if;
  return jsonb_build_object('n', n, 'created', fresh, 'duplicate', fresh = 0, 'request', p_request);
end;
$$;
revoke all on function public.admin_grant_v2(uuid[], boolean, bigint, bigint, text, uuid) from public, anon;
grant execute on function public.admin_grant_v2(uuid[], boolean, bigint, bigint, text, uuid) to authenticated;

create or replace function public.admin_message_v2(p_user_ids uuid[], p_all boolean, p_title text, p_body text, p_request uuid)
returns jsonb
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare v_admin uuid := public.codis_require_admin(); fresh int; n int;
begin
  if p_request is null then raise exception 'request id required' using errcode = '22023'; end if;
  p_title := trim(coalesce(p_title, '')); p_body := trim(coalesce(p_body, ''));
  if char_length(p_title) not between 1 and 120 then raise exception 'title must be 1-120 characters' using errcode = '22023'; end if;
  if char_length(p_body) not between 1 and 2000 then raise exception 'message must be 1-2000 characters' using errcode = '22023'; end if;
  insert into public.admin_messages(user_id, title, body, created_by, request_id)
  select t, p_title, p_body, v_admin, p_request from public.codis_admin_targets(p_user_ids, p_all) t
  on conflict (created_by, request_id, user_id) where request_id is not null do nothing;
  get diagnostics fresh = row_count;
  select count(*)::int into n from public.admin_messages m where m.created_by = v_admin and m.request_id = p_request;
  if fresh > 0 then
    insert into public.admin_audit(admin_id, action, targets, detail)
    values (v_admin, 'message', fresh, jsonb_build_object('title', p_title, 'all', coalesce(p_all, false), 'request', p_request));
  end if;
  return jsonb_build_object('n', n, 'created', fresh, 'duplicate', fresh = 0, 'request', p_request);
end;
$$;
revoke all on function public.admin_message_v2(uuid[], boolean, text, text, uuid) from public, anon;
grant execute on function public.admin_message_v2(uuid[], boolean, text, text, uuid) to authenticated;

-- gifts log with a real status: pending (not yet opened by the user) · applied (user's app applied it and acknowledged) · cancelled
drop function if exists public.admin_list_grants(text, text, int, int);
create or replace function public.admin_list_grants(p_status text default '', p_search text default '', p_limit int default 200, p_offset int default 0)
returns table (id uuid, user_id uuid, email text, full_name text, coins bigint, silver bigint, note text,
               created_at timestamptz, claimed_at timestamptz, cancelled_at timestamptz, status text)
language plpgsql
stable
security definer
set search_path = ''
as $$
declare s text := '%' || coalesce(trim(p_search), '') || '%';
begin
  perform public.codis_require_admin();
  return query
  select g.id, g.user_id, u.email::text, coalesce(u.raw_user_meta_data->>'full_name', u.raw_user_meta_data->>'name'),
         g.coins, g.silver, g.note, g.created_at, g.claimed_at, g.cancelled_at,
         case when g.cancelled_at is not null then 'cancelled' when g.claimed_at is not null then 'applied' else 'pending' end
    from public.admin_grants g left join auth.users u on u.id = g.user_id
   where (coalesce(p_status, '') = ''
          or (p_status = 'cancelled' and g.cancelled_at is not null)
          or (p_status = 'applied'   and g.cancelled_at is null and g.claimed_at is not null)
          or (p_status = 'pending'   and g.cancelled_at is null and g.claimed_at is null))
     and (coalesce(trim(p_search), '') = '' or u.email ilike s or g.note ilike s or coalesce(u.raw_user_meta_data->>'full_name', u.raw_user_meta_data->>'name', '') ilike s)
   order by g.created_at desc, g.id
   limit greatest(1, least(coalesce(p_limit, 200), 1000)) offset greatest(0, coalesce(p_offset, 0));
end;
$$;
revoke all on function public.admin_list_grants(text, text, int, int) from public, anon;
grant execute on function public.admin_list_grants(text, text, int, int) to authenticated;

drop function if exists public.admin_list_messages(text, text, int, int);
create or replace function public.admin_list_messages(p_status text default '', p_search text default '', p_limit int default 200, p_offset int default 0)
returns table (id uuid, user_id uuid, email text, full_name text, title text, body text, created_at timestamptz, delivered_at timestamptz, status text)
language plpgsql
stable
security definer
set search_path = ''
as $$
declare s text := '%' || coalesce(trim(p_search), '') || '%';
begin
  perform public.codis_require_admin();
  return query
  select m.id, m.user_id, u.email::text, coalesce(u.raw_user_meta_data->>'full_name', u.raw_user_meta_data->>'name'),
         m.title, m.body, m.created_at, m.delivered_at, case when m.delivered_at is not null then 'delivered' else 'pending' end
    from public.admin_messages m left join auth.users u on u.id = m.user_id
   where (coalesce(p_status, '') = '' or (p_status = 'delivered' and m.delivered_at is not null) or (p_status = 'pending' and m.delivered_at is null))
     and (coalesce(trim(p_search), '') = '' or u.email ilike s or m.title ilike s or m.body ilike s)
   order by m.created_at desc, m.id
   limit greatest(1, least(coalesce(p_limit, 200), 1000)) offset greatest(0, coalesce(p_offset, 0));
end;
$$;
revoke all on function public.admin_list_messages(text, text, int, int) from public, anon;
grant execute on function public.admin_list_messages(text, text, int, int) to authenticated;

notify pgrst, 'reload schema';
