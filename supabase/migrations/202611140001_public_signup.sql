-- Apply AFTER 202611130001_normalized_backend.sql. No hosted changes are automatic.
begin;
-- Auth owns email/password; reuse the existing profile table for application data.
-- The trigger runs in the same transaction as Auth creation: a failed profile
-- insert rolls back account creation. Never trust role/clinic metadata.
create or replace function public.netrava_register_profile()
returns trigger
language plpgsql security definer set search_path = ''
as $$
begin
  insert into public.user_profiles(id, full_name, role, clinic_id, is_active)
  values (new.id, coalesce(nullif(trim(new.raw_user_meta_data->>'full_name'), ''), 'New user'),
          'technician', null, false);
  return new;
end;
$$;
revoke all on function public.netrava_register_profile() from public, anon, authenticated;
drop trigger if exists netrava_register_profile on auth.users;
create trigger netrava_register_profile after insert on auth.users
for each row execute function public.netrava_register_profile();
commit;
