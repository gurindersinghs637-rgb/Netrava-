-- Apply after 202611140002_active_signup.sql.
-- Hosted clinics may enforce unique clinic names. The former constant name
-- prevented every signup after the first private workspace was created.
-- Preserve existing workspaces, profiles, privileges, RLS and the Auth trigger.
begin;

create or replace function public.netrava_register_profile()
returns trigger language plpgsql security definer set search_path = ''
as $$
declare workspace_id uuid;
begin
  insert into public.clinics(clinic_name, is_active)
  values ('Personal screening workspace - ' || new.id::text, true)
  returning id into workspace_id;

  insert into public.user_profiles(id, full_name, email, phone, role, clinic_id, is_active)
  values (new.id, coalesce(nullif(trim(new.raw_user_meta_data->>'full_name'), ''), 'New user'),
          new.email, new.raw_user_meta_data->>'phone', 'technician', workspace_id, true);
  return new;
end;
$$;

revoke all on function public.netrava_register_profile() from public, anon, authenticated;

commit;
