-- ============================================================
-- TRASH TO TREASURE - SUPABASE DATABASE SETUP
-- Run this in Supabase SQL Editor.
-- ============================================================

create extension if not exists pgcrypto;

-- ------------------------------------------------------------
-- PROFILES
-- ------------------------------------------------------------
create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    full_name text,
    role text not null default 'user'
        check (role in ('user', 'admin')),
    created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

revoke all on public.profiles from anon, authenticated;
grant select, insert, update on public.profiles to authenticated;

drop policy if exists "Users can read own profile" on public.profiles;
create policy "Users can read own profile"
on public.profiles
for select
to authenticated
using ((select auth.uid()) = id);

drop policy if exists "Users can insert own profile" on public.profiles;
create policy "Users can insert own profile"
on public.profiles
for insert
to authenticated
with check ((select auth.uid()) = id);

drop policy if exists "Users can update own profile" on public.profiles;
create policy "Users can update own profile"
on public.profiles
for update
to authenticated
using ((select auth.uid()) = id)
with check ((select auth.uid()) = id);


-- Automatically create profile after signup.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    insert into public.profiles (id, full_name)
    values (
        new.id,
        coalesce(new.raw_user_meta_data ->> 'full_name', '')
    )
    on conflict (id) do nothing;

    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;

create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_user();


-- ------------------------------------------------------------
-- SCRAP RATES
-- Publicly readable; admin-managed.
-- ------------------------------------------------------------
create table if not exists public.scrap_rates (
    id uuid primary key default gen_random_uuid(),
    material text unique not null,
    unit text not null default 'kg',
    rate numeric(12,2) not null check (rate >= 0),
    source text,
    active boolean not null default true,
    updated_at timestamptz not null default now()
);

alter table public.scrap_rates enable row level security;

revoke all on public.scrap_rates from anon, authenticated;
grant select on public.scrap_rates to anon, authenticated;
grant insert, update, delete on public.scrap_rates to authenticated;

drop policy if exists "Anyone can read active rates" on public.scrap_rates;
create policy "Anyone can read active rates"
on public.scrap_rates
for select
to anon, authenticated
using (active = true);

-- Admin write policy.
drop policy if exists "Admins manage rates" on public.scrap_rates;
create policy "Admins manage rates"
on public.scrap_rates
for all
to authenticated
using (
    exists (
        select 1 from public.profiles p
        where p.id = (select auth.uid())
        and p.role = 'admin'
    )
)
with check (
    exists (
        select 1 from public.profiles p
        where p.id = (select auth.uid())
        and p.role = 'admin'
    )
);


-- ------------------------------------------------------------
-- DEALERS
-- ------------------------------------------------------------
create table if not exists public.dealers (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    area text not null default 'Mianwali',
    address text,
    phone text not null,
    materials text[] not null default '{}',
    verified boolean not null default false,
    active boolean not null default true,
    created_at timestamptz not null default now()
);

alter table public.dealers enable row level security;

revoke all on public.dealers from anon, authenticated;
grant select on public.dealers to anon, authenticated;
grant insert, update, delete on public.dealers to authenticated;

drop policy if exists "Anyone can read verified dealers" on public.dealers;
create policy "Anyone can read verified dealers"
on public.dealers
for select
to anon, authenticated
using (verified = true and active = true);

drop policy if exists "Admins manage dealers" on public.dealers;
create policy "Admins manage dealers"
on public.dealers
for all
to authenticated
using (
    exists (
        select 1 from public.profiles p
        where p.id = (select auth.uid())
        and p.role = 'admin'
    )
)
with check (
    exists (
        select 1 from public.profiles p
        where p.id = (select auth.uid())
        and p.role = 'admin'
    )
);


-- ------------------------------------------------------------
-- SCRAP RECORDS
-- PRIVATE: each user sees only their own rows.
-- ------------------------------------------------------------
create table if not exists public.scrap_records (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    image_path text,
    material text,
    category text not null,
    confidence integer check (confidence between 0 and 100),
    condition text,
    quantity numeric(12,3) not null check (quantity > 0),
    unit text not null default 'kg',
    rate numeric(12,2),
    estimated_value numeric(14,2),
    created_at timestamptz not null default now()
);

create index if not exists scrap_records_user_id_idx
on public.scrap_records(user_id);

alter table public.scrap_records enable row level security;

revoke all on public.scrap_records from anon, authenticated;
grant select, insert, update, delete on public.scrap_records to authenticated;

drop policy if exists "Users read own scrap records" on public.scrap_records;
create policy "Users read own scrap records"
on public.scrap_records
for select
to authenticated
using ((select auth.uid()) = user_id);

drop policy if exists "Users insert own scrap records" on public.scrap_records;
create policy "Users insert own scrap records"
on public.scrap_records
for insert
to authenticated
with check ((select auth.uid()) = user_id);

drop policy if exists "Users update own scrap records" on public.scrap_records;
create policy "Users update own scrap records"
on public.scrap_records
for update
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

drop policy if exists "Users delete own scrap records" on public.scrap_records;
create policy "Users delete own scrap records"
on public.scrap_records
for delete
to authenticated
using ((select auth.uid()) = user_id);


-- ------------------------------------------------------------
-- PRIVATE STORAGE BUCKET
-- ------------------------------------------------------------
insert into storage.buckets (id, name, public)
values ('scrap-images', 'scrap-images', false)
on conflict (id) do nothing;

-- User can upload only inside their own UUID folder.
drop policy if exists "Users upload own scrap images"
on storage.objects;

create policy "Users upload own scrap images"
on storage.objects
for insert
to authenticated
with check (
    bucket_id = 'scrap-images'
    and (storage.foldername(name))[1] = (select auth.uid())::text
);

drop policy if exists "Users read own scrap images"
on storage.objects;

create policy "Users read own scrap images"
on storage.objects
for select
to authenticated
using (
    bucket_id = 'scrap-images'
    and (storage.foldername(name))[1] = (select auth.uid())::text
);

drop policy if exists "Users delete own scrap images"
on storage.objects;

create policy "Users delete own scrap images"
on storage.objects
for delete
to authenticated
using (
    bucket_id = 'scrap-images'
    and (storage.foldername(name))[1] = (select auth.uid())::text
);


-- ------------------------------------------------------------
-- STARTER RATES
-- IMPORTANT: THESE ARE PLACEHOLDER/DEMO VALUES.
-- Replace with verified current Pakistan rates.
-- ------------------------------------------------------------
insert into public.scrap_rates
(material, unit, rate, source)
values
('Iron / Steel', 'kg', 100, 'DEMO - replace'),
('Aluminium', 'kg', 225, 'DEMO - replace'),
('Copper', 'kg', 1650, 'DEMO - replace'),
('Brass', 'kg', 1000, 'DEMO - replace'),
('Stainless Steel', 'kg', 180, 'DEMO - replace'),
('Cardboard', 'kg', 30, 'DEMO - replace'),
('Newspaper', 'kg', 40, 'DEMO - replace'),
('Mixed Paper', 'kg', 30, 'DEMO - replace'),
('PET Plastic', 'kg', 70, 'DEMO - replace'),
('Hard Plastic', 'kg', 60, 'DEMO - replace'),
('Mixed Plastic', 'kg', 50, 'DEMO - replace'),
('E-Waste', 'kg', 150, 'DEMO - replace'),
('Cotton Cloth', 'kg', 80, 'DEMO - replace'),
('Denim', 'kg', 70, 'DEMO - replace'),
('Mixed Textile', 'kg', 50, 'DEMO - replace'),
('Textile Rags', 'kg', 60, 'DEMO - replace'),
('Battery', 'kg', 0, 'Dealer quotation required')
on conflict (material) do nothing;


-- ------------------------------------------------------------
-- EXAMPLE DEALER RECORDS
-- IMPORTANT:
-- Verify each dealer, phone number, materials and permission
-- before setting verified=true.
-- ------------------------------------------------------------
insert into public.dealers
(name, area, phone, materials, verified, active)
values
(
    'Shah G Scrap Dealers Mianwali',
    'Mianwali',
    '+923706000509',
    ARRAY['Iron / Steel','Aluminium','Copper','Brass','E-Waste'],
    false,
    true
),
(
    'Ghulam Qasim & Sons Old Scrap Dealer',
    'Mianwali',
    '+923261878005',
    ARRAY['Iron / Steel','Aluminium','Copper','Brass'],
    false,
    true
),
(
    'Kabar Shop',
    'Kundian',
    '+923217171524',
    ARRAY['Iron / Steel','Aluminium','Copper','Mixed Plastic'],
    false,
    true
)
on conflict do nothing;


-- ============================================================
-- ADMIN SETUP
-- ============================================================
-- After creating your own account in the app, run:
--
-- update public.profiles
-- set role = 'admin'
-- where id = 'YOUR-SUPABASE-USER-UUID';
--
-- Do NOT put a service-role/secret key in Streamlit Cloud
-- if the normal authenticated client can perform the task.
-- ============================================================
