-- Apply after the normalized schema and 202611140001_public_signup.sql.
-- Each new account gets an isolated workspace, never a shared demo clinic.
begin;
alter table public.user_profiles add column if not exists email text;
alter table public.user_profiles add column if not exists phone text;

create or replace function public.netrava_register_profile()
returns trigger language plpgsql security definer set search_path = ''
as $$
declare workspace_id uuid;
begin
  insert into public.clinics(clinic_name, is_active)
  values ('Personal screening workspace', true) returning id into workspace_id;
  insert into public.user_profiles(id, full_name, email, phone, role, clinic_id, is_active)
  values (new.id, coalesce(nullif(trim(new.raw_user_meta_data->>'full_name'), ''), 'New user'),
          new.email, new.raw_user_meta_data->>'phone', 'technician', workspace_id, true);
  return new;
end;
$$;
revoke all on function public.netrava_register_profile() from public, anon, authenticated;
drop trigger if exists netrava_register_profile on auth.users;
create trigger netrava_register_profile after insert on auth.users
for each row execute function public.netrava_register_profile();
-- Existing disabled/pending accounts are intentionally unchanged.
commit;
