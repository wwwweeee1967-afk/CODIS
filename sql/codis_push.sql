-- =====================================================================
-- CODIS — Web Push for timer endings (idempotent: safe to run more than once)
-- Run in: Supabase Dashboard → SQL Editor (as `postgres`), AFTER codis_supabase_setup.sql.
--
-- What the app calls (CodisAccount.pushCall → POST /rest/v1/rpc/<name>):
--   push_subscribe(p_endpoint, p_p256dh, p_auth, p_ua)      register this device
--   push_unsubscribe(p_endpoint)                            remove this device
--   push_schedule(p_event_id, p_fire_at, p_title, p_body)   a timer started → send at fire_at
--   push_cancel(p_event_id)                                 timer stopped / ended in the open app
-- What the Edge Function calls (service_role only):
--   push_claim_due(p_limit)  → atomically claims due timers (sent_at set once) + their subscriptions
--   push_drop_endpoint(p_endpoint)  → removes a subscription the push service reports as gone (404/410)
--
-- Security model (same as the rest of CODIS): RLS on, no direct table access for anon/authenticated,
-- every write is a SECURITY DEFINER function that takes the owner from auth.uid() — never from the client.
-- A user can never read, schedule for, or send to another user's devices. The VAPID private key and the
-- service_role key live ONLY in Edge Function secrets; nothing secret is stored in these tables.
-- =====================================================================

-- ---------- 1) device subscriptions ----------
create table if not exists public.push_subscriptions (
  endpoint    text primary key,
  user_id     uuid not null references auth.users(id) on delete cascade,
  p256dh      text not null,
  auth        text not null,
  ua          text,
  created_at  timestamptz not null default now(),
  last_ok_at  timestamptz
);
create index if not exists push_subscriptions_user_idx on public.push_subscriptions(user_id);
alter table public.push_subscriptions enable row level security;
revoke all on public.push_subscriptions from public, anon, authenticated;

-- ---------- 2) scheduled timer notifications (one row per timer event id) ----------
create table if not exists public.push_timers (
  event_id     text primary key,
  user_id      uuid not null references auth.users(id) on delete cascade,
  fire_at      timestamptz not null,
  title        text not null,
  body         text not null,
  created_at   timestamptz not null default now(),
  sent_at      timestamptz,          -- set exactly once by push_claim_due (dedupe across cron reruns)
  cancelled_at timestamptz           -- set by push_cancel (timer stopped, or the open app already showed it)
);
create index if not exists push_timers_due_idx on public.push_timers(fire_at) where sent_at is null and cancelled_at is null;
alter table public.push_timers enable row level security;
revoke all on public.push_timers from public, anon, authenticated;

-- ---------- 3) client RPCs (owner = auth.uid()) ----------
create or replace function public.push_subscribe(p_endpoint text, p_p256dh text, p_auth text, p_ua text default null)
returns void language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid();
begin
  if uid is null then raise exception 'not signed in' using errcode = '28000'; end if;
  if p_endpoint is null or p_endpoint !~ '^https://' or length(p_endpoint) > 1000
     or coalesce(length(p_p256dh), 0) not between 40 and 200 or coalesce(length(p_auth), 0) not between 10 and 100 then
    raise exception 'invalid subscription' using errcode = '22023';
  end if;
  if (select count(*) from push_subscriptions where user_id = uid and endpoint <> p_endpoint) >= 20 then
    delete from push_subscriptions where endpoint in (select endpoint from push_subscriptions where user_id = uid order by created_at limit 1);
  end if;
  insert into push_subscriptions(endpoint, user_id, p256dh, auth, ua)
  values (p_endpoint, uid, p_p256dh, p_auth, left(p_ua, 200))
  on conflict (endpoint) do update set user_id = excluded.user_id, p256dh = excluded.p256dh, auth = excluded.auth, ua = excluded.ua, created_at = now();
end $$;

create or replace function public.push_unsubscribe(p_endpoint text)
returns void language sql security definer set search_path = public as $$
  delete from push_subscriptions where endpoint = p_endpoint and user_id = auth.uid();
$$;

create or replace function public.push_schedule(p_event_id text, p_fire_at timestamptz, p_title text, p_body text)
returns void language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid();
begin
  if uid is null then raise exception 'not signed in' using errcode = '28000'; end if;
  if p_event_id !~ '^ev_[a-z0-9]{6,40}$' then raise exception 'invalid event id' using errcode = '22023'; end if;
  if p_fire_at < now() - interval '1 minute' or p_fire_at > now() + interval '25 hours' then raise exception 'invalid time' using errcode = '22023'; end if;
  if (select count(*) from push_timers where user_id = uid and sent_at is null and cancelled_at is null) >= 200 then
    raise exception 'too many pending timers' using errcode = '54000';
  end if;
  insert into push_timers(event_id, user_id, fire_at, title, body)
  values (p_event_id, uid, p_fire_at, left(coalesce(p_title, 'CODIS'), 80), left(coalesce(p_body, ''), 240))
  on conflict (event_id) do update set fire_at = excluded.fire_at, title = excluded.title, body = excluded.body
    where push_timers.user_id = uid and push_timers.sent_at is null;   -- another user's id is never touched
end $$;

create or replace function public.push_cancel(p_event_id text)
returns void language sql security definer set search_path = public as $$
  update push_timers set cancelled_at = now()
   where event_id = p_event_id and user_id = auth.uid() and sent_at is null and cancelled_at is null;
$$;

revoke all on function public.push_subscribe(text, text, text, text), public.push_unsubscribe(text),
  public.push_schedule(text, timestamptz, text, text), public.push_cancel(text) from public, anon;
grant execute on function public.push_subscribe(text, text, text, text), public.push_unsubscribe(text),
  public.push_schedule(text, timestamptz, text, text), public.push_cancel(text) to authenticated;

-- ---------- 4) sender RPCs (service_role only — used by the Edge Function) ----------
create or replace function public.push_claim_due(p_limit int default 200)
returns table(event_id text, title text, body text, endpoint text, p256dh text, auth text)
language plpgsql security definer set search_path = public as $$
begin
  return query
  with due as (
    select t.event_id from push_timers t
     where t.sent_at is null and t.cancelled_at is null and t.fire_at <= now()
     order by t.fire_at limit greatest(1, least(p_limit, 500))
     for update skip locked
  ), claimed as (
    update push_timers t set sent_at = now() from due where t.event_id = due.event_id
    returning t.event_id, t.user_id, t.title, t.body
  )
  select c.event_id, c.title, c.body, s.endpoint, s.p256dh, s.auth
    from claimed c join push_subscriptions s on s.user_id = c.user_id;
  delete from push_timers where coalesce(sent_at, cancelled_at) < now() - interval '14 days';
end $$;

create or replace function public.push_drop_endpoint(p_endpoint text)
returns void language sql security definer set search_path = public as $$
  delete from push_subscriptions where endpoint = p_endpoint;
$$;

revoke all on function public.push_claim_due(int), public.push_drop_endpoint(text) from public, anon, authenticated;
grant execute on function public.push_claim_due(int), public.push_drop_endpoint(text) to service_role;

-- ---------- 5) schedule: every minute, call the Edge Function (needs pg_cron + pg_net + Vault) ----------
-- Run this block ONCE after deploying the function and storing two Vault secrets (see docs/CODIS_PUSH_SETUP.md):
--   codis_push_url          = https://<project-ref>.supabase.co/functions/v1/codis-push
--   codis_push_cron_secret  = the same random value you set as the CODIS_CRON_SECRET function secret
--
-- create extension if not exists pg_cron;
-- create extension if not exists pg_net;
-- select cron.unschedule('codis-push-due') where exists (select 1 from cron.job where jobname = 'codis-push-due');
-- select cron.schedule('codis-push-due', '* * * * *', $cron$
--   select net.http_post(
--     url     := (select decrypted_secret from vault.decrypted_secrets where name = 'codis_push_url'),
--     headers := jsonb_build_object('Content-Type', 'application/json',
--                  'x-codis-cron', (select decrypted_secret from vault.decrypted_secrets where name = 'codis_push_cron_secret')),
--     body    := '{}'::jsonb);
-- $cron$);
