-- CODIS hardening v38 (3.25.0) — security audit fixes for the push RPCs. Idempotent; run once in the SQL editor or as a migration
-- AFTER codis_push.sql and codis_push_v2.sql. Changes NO data, NO tables, NO grants (except one new index).
--
-- 1) search_path: every SECURITY DEFINER push function now runs with `set search_path = ''` and fully-qualified names
--    (was `= public`: an object created in schema public could shadow push_timers/push_subscriptions inside a definer function).
--    Behaviour is byte-for-byte the same; only name resolution is hardened. Same pattern as save_progress/is_admin already use.
-- 2) push_subscribe takeover: re-binding an existing endpoint to ANOTHER account now requires the same encryption keys
--    (p256dh + auth). Only the browser that owns the subscription knows them, so a genuine account switch on the same device
--    still works, but someone who merely learned the endpoint URL can no longer steal another user's notifications.
-- 3) performance advisor: covering index for push_timers.user_id (foreign key without index).

create or replace function public.push_subscribe(p_endpoint text, p_p256dh text, p_auth text, p_ua text default null)
returns void language plpgsql security definer set search_path = '' as $$
declare uid uuid := auth.uid();
begin
  if uid is null then raise exception 'not signed in' using errcode = '28000'; end if;
  if p_endpoint is null or p_endpoint !~ '^https://' or length(p_endpoint) > 1000
     or coalesce(length(p_p256dh), 0) not between 40 and 200 or coalesce(length(p_auth), 0) not between 10 and 100 then
    raise exception 'invalid subscription' using errcode = '22023';
  end if;
  if (select count(*) from public.push_subscriptions where user_id = uid and endpoint <> p_endpoint) >= 20 then
    delete from public.push_subscriptions where endpoint in (select endpoint from public.push_subscriptions where user_id = uid order by created_at limit 1);
  end if;
  insert into public.push_subscriptions(endpoint, user_id, p256dh, auth, ua)
  values (p_endpoint, uid, p_p256dh, p_auth, left(p_ua, 200))
  on conflict (endpoint) do update set user_id = excluded.user_id, p256dh = excluded.p256dh, auth = excluded.auth, ua = excluded.ua, created_at = now()
    where public.push_subscriptions.user_id = uid
       or (public.push_subscriptions.p256dh = excluded.p256dh and public.push_subscriptions.auth = excluded.auth);   -- v38: proof of possession
end $$;

create or replace function public.push_unsubscribe(p_endpoint text)
returns void language sql security definer set search_path = '' as $$
  delete from public.push_subscriptions where endpoint = p_endpoint and user_id = auth.uid();
$$;

create or replace function public.push_schedule(p_event_id text, p_fire_at timestamptz, p_title text, p_body text)
returns void language plpgsql security definer set search_path = '' as $$
declare uid uuid := auth.uid();
begin
  if uid is null then raise exception 'not signed in' using errcode = '28000'; end if;
  if p_event_id !~ '^ev_[a-z0-9]{6,40}$' then raise exception 'invalid event id' using errcode = '22023'; end if;
  if p_fire_at < now() - interval '1 minute' or p_fire_at > now() + interval '8 days' then raise exception 'invalid time' using errcode = '22023'; end if;
  if (select count(*) from public.push_timers where user_id = uid and sent_at is null and cancelled_at is null) >= 400 then
    raise exception 'too many pending timers' using errcode = '54000';
  end if;
  insert into public.push_timers(event_id, user_id, fire_at, title, body)
  values (p_event_id, uid, p_fire_at, left(coalesce(p_title, 'CODIS'), 80), left(coalesce(p_body, ''), 240))
  on conflict (event_id) do update set fire_at = excluded.fire_at, title = excluded.title, body = excluded.body, cancelled_at = null
    where public.push_timers.user_id = uid and public.push_timers.sent_at is null;
end $$;

create or replace function public.push_cancel(p_event_id text)
returns void language sql security definer set search_path = '' as $$
  update public.push_timers set cancelled_at = now()
   where event_id = p_event_id and user_id = auth.uid() and sent_at is null and cancelled_at is null;
$$;

create or replace function public.push_claim_due(p_limit int default 200)
returns table(event_id text, title text, body text, endpoint text, p256dh text, auth text)
language plpgsql security definer set search_path = '' as $$
begin
  return query
  with due as (
    select t.event_id from public.push_timers t
     where t.sent_at is null and t.cancelled_at is null and t.fire_at <= now()
     order by t.fire_at limit greatest(1, least(p_limit, 500))
     for update skip locked
  ), claimed as (
    update public.push_timers t set sent_at = now() from due where t.event_id = due.event_id
    returning t.event_id, t.user_id, t.title, t.body
  )
  select c.event_id, c.title, c.body, s.endpoint, s.p256dh, s.auth
    from claimed c join public.push_subscriptions s on s.user_id = c.user_id;
  delete from public.push_timers where coalesce(sent_at, cancelled_at) < now() - interval '14 days';
end $$;

create or replace function public.push_drop_endpoint(p_endpoint text)
returns void language sql security definer set search_path = '' as $$
  delete from public.push_subscriptions where endpoint = p_endpoint;
$$;

create or replace function public.push_vapid_public()
returns text language sql stable security definer set search_path = '' as $$
  select decrypted_secret from vault.decrypted_secrets where name = 'codis_vapid_public' limit 1;
$$;

create or replace function public.push_keys()
returns table(pub text, priv text, cron text) language sql stable security definer set search_path = '' as $$
  select (select decrypted_secret from vault.decrypted_secrets where name = 'codis_vapid_public' limit 1),
         (select decrypted_secret from vault.decrypted_secrets where name = 'codis_vapid_private' limit 1),
         (select decrypted_secret from vault.decrypted_secrets where name = 'codis_push_cron_secret' limit 1);
$$;

create or replace function public.push_keys_init(p_pub text, p_priv text)
returns boolean language plpgsql security definer set search_path = '' as $$
begin
  if p_pub !~ '^[A-Za-z0-9_-]{80,100}$' or p_priv !~ '^[A-Za-z0-9_-]{40,50}$' then raise exception 'invalid key' using errcode = '22023'; end if;
  if exists (select 1 from vault.secrets where name = 'codis_vapid_public') then return false; end if;
  begin
    perform vault.create_secret(p_priv, 'codis_vapid_private');
    perform vault.create_secret(p_pub, 'codis_vapid_public');
  exception when unique_violation then return false;
  end;
  return true;
end $$;

create index if not exists push_timers_user_id_idx on public.push_timers(user_id);

-- grants re-asserted explicitly (identical to codis_push.sql / v2): CREATE OR REPLACE keeps existing grants, but if a function did not
-- exist yet Postgres would grant EXECUTE to PUBLIC by default — so this file must never rely on run order.
revoke all on function public.push_subscribe(text, text, text, text), public.push_unsubscribe(text),
  public.push_schedule(text, timestamptz, text, text), public.push_cancel(text) from public, anon;
grant execute on function public.push_subscribe(text, text, text, text), public.push_unsubscribe(text),
  public.push_schedule(text, timestamptz, text, text), public.push_cancel(text) to authenticated;
revoke all on function public.push_claim_due(int), public.push_drop_endpoint(text) from public, anon, authenticated;
grant execute on function public.push_claim_due(int), public.push_drop_endpoint(text) to service_role;
revoke all on function public.push_vapid_public() from public;
grant execute on function public.push_vapid_public() to anon, authenticated, service_role;
revoke all on function public.push_keys(), public.push_keys_init(text, text) from public, anon, authenticated;
grant execute on function public.push_keys(), public.push_keys_init(text, text) to service_role;
