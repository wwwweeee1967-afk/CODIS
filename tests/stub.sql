create role anon nologin; create role authenticated nologin;
create schema auth; create schema storage;
create table auth.users(id uuid primary key default gen_random_uuid(), email text);
create function auth.uid() returns uuid language sql stable as $$
  select coalesce(nullif(current_setting('request.jwt.claim.sub',true),''),
                  (nullif(current_setting('request.jwt.claims',true),'')::jsonb ->> 'sub'))::uuid $$;
create table storage.buckets(id text primary key, name text, public boolean default false);
create table storage.objects(id uuid default gen_random_uuid() primary key, bucket_id text, name text);
alter table storage.objects enable row level security;
grant usage on schema auth, storage, public to anon, authenticated;
grant execute on function auth.uid() to anon, authenticated;
grant select on storage.objects to anon, authenticated;
