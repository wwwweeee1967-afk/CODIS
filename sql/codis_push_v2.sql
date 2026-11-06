-- CODIS push v2 (3.21.0) — تذكيرات العادات الخلفية (23:00 اليومي + يوم العادة الأسبوعية 09:00).
-- يعيد استعمال جدول push_timers ومرسل codis-push الموجودين: كل تذكير صف بمعرّف فريد ev_<...> (مستخدم + تاريخ [+ عادة]) يُرسَل مرة واحدة من الخادم عبر pg_cron
-- حتى والتطبيق مغلق. الفرق الوحيد عن v1: نافذة الجدولة 8 أيام بدل 25 ساعة، وسقف المعلّق 400 بدل 200 (التطبيق يجدول 7 أيام قادمة).
-- idempotent — شغّله مرة واحدة في SQL editor أو كـmigration. لا يغيّر الجداول ولا الصلاحيات.
create or replace function public.push_schedule(p_event_id text, p_fire_at timestamptz, p_title text, p_body text)
returns void language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid();
begin
  if uid is null then raise exception 'not signed in' using errcode = '28000'; end if;
  if p_event_id !~ '^ev_[a-z0-9]{6,40}$' then raise exception 'invalid event id' using errcode = '22023'; end if;
  if p_fire_at < now() - interval '1 minute' or p_fire_at > now() + interval '8 days' then raise exception 'invalid time' using errcode = '22023'; end if;
  if (select count(*) from push_timers where user_id = uid and sent_at is null and cancelled_at is null) >= 400 then
    raise exception 'too many pending timers' using errcode = '54000';
  end if;
  insert into push_timers(event_id, user_id, fire_at, title, body)
  values (p_event_id, uid, p_fire_at, left(coalesce(p_title, 'CODIS'), 80), left(coalesce(p_body, ''), 240))
  on conflict (event_id) do update set fire_at = excluded.fire_at, title = excluded.title, body = excluded.body, cancelled_at = null
    where push_timers.user_id = uid and push_timers.sent_at is null;   -- صف مستخدم آخر لا يُمَس أبداً؛ المُرسَل لا يُعاد إرساله
end $$;
revoke all on function public.push_schedule(text, timestamptz, text, text) from public, anon;
grant execute on function public.push_schedule(text, timestamptz, text, text) to authenticated;
