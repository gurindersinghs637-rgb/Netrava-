-- OWNER APPROVAL REQUIRED: targeted repair for the existing signup account.
-- First deploy reviewed 202611140002_active_signup.sql for FUTURE registrations.
-- Run this entire transaction in the intended Supabase SQL Editor.
-- No password, Auth confirmation state, or existing clinic membership is changed.
begin;
do $$
declare account_id uuid; workspace_id uuid; current_profile public.user_profiles;
begin
  select id into strict account_id from auth.users
    where lower(email) = 'preamgills232@gmail.com';
  select * into strict current_profile from public.user_profiles
    where id = account_id for update;
  if current_profile.role <> 'technician' then
    raise exception 'Refusing to alter a non-technician account';
  end if;
  if current_profile.clinic_id is not null then
    raise exception 'Account already has a workspace; review manually';
  end if;
  insert into public.clinics(clinic_name,is_active)
    values('Personal screening workspace',true) returning id into workspace_id;
  update public.user_profiles
    set full_name='Gurinder Singh', email='preamgills232@gmail.com',
        phone='7087655575', clinic_id=workspace_id, is_active=true, updated_at=now()
    where id=account_id;
end $$;
commit;
