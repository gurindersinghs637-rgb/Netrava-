-- NETRAVA backend foundation. Apply only to a reviewed Supabase project.
-- All medical records are clinic scoped. Server-side service-role queries
-- must still include the authenticated clinic_id; RLS protects direct clients.

create table if not exists public.clinics (
    id uuid primary key default gen_random_uuid(),
    name text not null check (length(trim(name)) between 1 and 200),
    created_at timestamptz not null default now()
);

create table if not exists public.user_profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    clinic_id uuid not null references public.clinics(id),
    role text not null check (role in ('technician', 'ophthalmologist', 'administrator')),
    full_name text not null default '',
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.patients (
    id uuid primary key default gen_random_uuid(),
    clinic_id uuid not null references public.clinics(id),
    mrn text not null,
    full_name text not null,
    date_of_birth date not null,
    gender text not null check (gender in ('male', 'female', 'other')),
    phone_number text,
    diabetes_type text not null check (diabetes_type in ('type_1', 'type_2', 'gestational', 'other')),
    diabetes_duration_years integer check (diabetes_duration_years between 0 and 100),
    latest_hba1c numeric(4, 2) check (latest_hba1c between 3 and 20),
    is_insulin_dependent boolean not null default false,
    notes text,
    registered_by uuid not null references public.user_profiles(id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (clinic_id, mrn)
);

create table if not exists public.screenings (
    id uuid primary key default gen_random_uuid(),
    clinic_id uuid not null references public.clinics(id),
    patient_id uuid not null references public.patients(id),
    technician_id uuid not null references public.user_profiles(id),
    status text not null default 'pending_review' check (status in ('pending_review', 'reviewed', 'completed')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.retinal_images (
    id uuid primary key default gen_random_uuid(),
    clinic_id uuid not null references public.clinics(id),
    screening_id uuid not null references public.screenings(id) on delete cascade,
    eye text not null check (eye in ('OD', 'OS')),
    storage_path text not null,
    is_gradable boolean not null,
    blur_score double precision not null,
    illumination text not null,
    qc_confidence double precision not null check (qc_confidence between 0 and 1),
    created_at timestamptz not null default now()
);

create table if not exists public.predictions (
    id uuid primary key default gen_random_uuid(),
    clinic_id uuid not null references public.clinics(id),
    retinal_image_id uuid not null references public.retinal_images(id) on delete cascade,
    predicted_grade smallint not null check (predicted_grade between 0 and 4),
    severity_label text not null,
    confidence_score double precision not null check (confidence_score between 0 and 1),
    inference_time_ms double precision not null check (inference_time_ms >= 0),
    probabilities jsonb not null check (jsonb_typeof(probabilities) = 'array'),
    gradcam_heatmap_path text,
    is_referral_recommended boolean not null,
    requested_by uuid not null references public.user_profiles(id),
    created_at timestamptz not null default now()
);

create table if not exists public.reports (
    id uuid primary key default gen_random_uuid(),
    clinic_id uuid not null references public.clinics(id),
    screening_id uuid not null references public.screenings(id) on delete cascade,
    prediction_id uuid references public.predictions(id),
    ophthalmologist_id uuid not null references public.user_profiles(id),
    overall_grade smallint not null check (overall_grade between 0 and 4),
    grade_override smallint check (grade_override between 0 and 4),
    ophthalmologist_notes text,
    is_urgent_referral boolean not null default false,
    is_signed_off boolean not null default false,
    signed_off_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (screening_id)
);

create table if not exists public.audit_logs (
    id uuid primary key default gen_random_uuid(),
    clinic_id uuid not null references public.clinics(id),
    actor_id uuid references public.user_profiles(id),
    action text not null,
    resource_type text not null,
    resource_id uuid,
    details jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_patients_clinic_created on public.patients(clinic_id, created_at desc);
create index if not exists idx_patients_clinic_mrn on public.patients(clinic_id, mrn);
create index if not exists idx_screenings_clinic_created on public.screenings(clinic_id, created_at desc);
create index if not exists idx_screenings_patient on public.screenings(patient_id, created_at desc);
create index if not exists idx_retinal_images_screening on public.retinal_images(screening_id);
create index if not exists idx_predictions_image_created on public.predictions(retinal_image_id, created_at desc);
create index if not exists idx_reports_screening on public.reports(screening_id, created_at desc);
create index if not exists idx_audit_clinic_created on public.audit_logs(clinic_id, created_at desc);

create or replace function public.current_user_clinic_id()
returns uuid
language sql
stable
security definer
set search_path = public
as $$
    select clinic_id from public.user_profiles
    where id = auth.uid() and active = true
$$;

alter table public.user_profiles enable row level security;
alter table public.clinics enable row level security;
alter table public.patients enable row level security;
alter table public.screenings enable row level security;
alter table public.retinal_images enable row level security;
alter table public.predictions enable row level security;
alter table public.reports enable row level security;
alter table public.audit_logs enable row level security;

create policy user_profiles_read_same_clinic on public.user_profiles
    for select to authenticated using (clinic_id = public.current_user_clinic_id());
create policy clinics_read_own on public.clinics
    for select to authenticated using (id = public.current_user_clinic_id());
create policy patients_read_same_clinic on public.patients
    for select to authenticated using (clinic_id = public.current_user_clinic_id());
create policy patients_insert_same_clinic on public.patients
    for insert to authenticated with check (clinic_id = public.current_user_clinic_id());
create policy patients_update_same_clinic on public.patients
    for update to authenticated using (clinic_id = public.current_user_clinic_id()) with check (clinic_id = public.current_user_clinic_id());
create policy screenings_clinic_access on public.screenings
    for all to authenticated using (clinic_id = public.current_user_clinic_id()) with check (clinic_id = public.current_user_clinic_id());
create policy retinal_images_clinic_access on public.retinal_images
    for all to authenticated using (clinic_id = public.current_user_clinic_id()) with check (clinic_id = public.current_user_clinic_id());
create policy predictions_clinic_read on public.predictions
    for select to authenticated using (clinic_id = public.current_user_clinic_id());
create policy reports_clinic_read on public.reports
    for select to authenticated using (clinic_id = public.current_user_clinic_id());
create policy reports_clinic_insert on public.reports
    for insert to authenticated with check (
        clinic_id = public.current_user_clinic_id()
        and exists (select 1 from public.user_profiles p where p.id = auth.uid() and p.role = 'ophthalmologist')
    );
create policy reports_clinic_update on public.reports
    for update to authenticated using (
        clinic_id = public.current_user_clinic_id()
        and exists (select 1 from public.user_profiles p where p.id = auth.uid() and p.role = 'ophthalmologist')
    ) with check (clinic_id = public.current_user_clinic_id());
create policy audit_logs_read_same_clinic on public.audit_logs
    for select to authenticated using (clinic_id = public.current_user_clinic_id());
create policy audit_logs_insert_same_clinic on public.audit_logs
    for insert to authenticated with check (clinic_id = public.current_user_clinic_id());

revoke insert, update, delete on public.audit_logs from public, anon, authenticated;
grant select on public.audit_logs to authenticated;

revoke insert, update, delete on public.user_profiles, public.patients, public.screenings,
    public.retinal_images, public.predictions, public.reports, public.clinics
    from public, anon, authenticated;
grant select on public.user_profiles, public.patients, public.screenings,
    public.retinal_images, public.predictions, public.reports, public.clinics
    to authenticated;
grant all on public.user_profiles, public.patients, public.screenings,
    public.retinal_images, public.predictions, public.reports, public.audit_logs, public.clinics
    to service_role;

create or replace function public.write_screening_review(
    p_screening_id uuid,
    p_clinic_id uuid,
    p_ophthalmologist_id uuid,
    p_overall_grade smallint,
    p_grade_override smallint,
    p_ophthalmologist_notes text,
    p_is_urgent_referral boolean,
    p_is_signed_off boolean
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_report public.reports;
    v_prediction_id uuid;
begin
    if not exists (
        select 1 from public.user_profiles
        where id = p_ophthalmologist_id
          and clinic_id = p_clinic_id
          and role = 'ophthalmologist'
          and active = true
    ) then
        raise exception 'Active ophthalmologist profile required';
    end if;

    if not exists (
        select 1 from public.screenings
        where id = p_screening_id and clinic_id = p_clinic_id
    ) then
        raise exception 'Screening not found in clinic';
    end if;

    select * into v_report
    from public.reports
    where screening_id = p_screening_id and clinic_id = p_clinic_id
    for update;
    if found and v_report.is_signed_off then
        if v_report.ophthalmologist_id = p_ophthalmologist_id
           and v_report.overall_grade = p_overall_grade
           and v_report.grade_override is not distinct from p_grade_override
           and v_report.ophthalmologist_notes is not distinct from p_ophthalmologist_notes
           and v_report.is_urgent_referral = p_is_urgent_referral
           and p_is_signed_off then
            return to_jsonb(v_report);
        end if;
        raise exception 'Signed report is immutable';
    end if;

    select id into v_prediction_id
    from public.predictions
    where clinic_id = p_clinic_id
      and retinal_image_id in (
          select id from public.retinal_images where screening_id = p_screening_id
      )
    order by created_at desc
    limit 1;

    insert into public.reports (
        clinic_id, screening_id, prediction_id, ophthalmologist_id,
        overall_grade, grade_override, ophthalmologist_notes,
        is_urgent_referral, is_signed_off, signed_off_at
    ) values (
        p_clinic_id, p_screening_id, v_prediction_id, p_ophthalmologist_id,
        p_overall_grade, p_grade_override, p_ophthalmologist_notes,
        p_is_urgent_referral, p_is_signed_off,
        case when p_is_signed_off then now() else null end
    )
    on conflict (screening_id) do update set
        prediction_id = excluded.prediction_id,
        ophthalmologist_id = excluded.ophthalmologist_id,
        overall_grade = excluded.overall_grade,
        grade_override = excluded.grade_override,
        ophthalmologist_notes = excluded.ophthalmologist_notes,
        is_urgent_referral = excluded.is_urgent_referral,
        is_signed_off = excluded.is_signed_off,
        signed_off_at = excluded.signed_off_at,
        updated_at = now()
    returning * into v_report;

    update public.screenings
    set status = case when p_is_signed_off then 'completed' else 'reviewed' end,
        updated_at = now()
    where id = p_screening_id and clinic_id = p_clinic_id;

    insert into public.audit_logs (
        clinic_id, actor_id, action, resource_type, resource_id, details
    ) values (
        p_clinic_id, p_ophthalmologist_id, 'screening.reviewed', 'report', v_report.id,
        jsonb_build_object(
            'screening_id', p_screening_id,
            'overall_grade', p_overall_grade,
            'grade_override', p_grade_override,
            'is_urgent_referral', p_is_urgent_referral,
            'is_signed_off', p_is_signed_off
        )
    );

    return to_jsonb(v_report);
end;
$$;

revoke all on function public.write_screening_review(uuid, uuid, uuid, smallint, smallint, text, boolean, boolean) from public, anon, authenticated;
grant execute on function public.write_screening_review(uuid, uuid, uuid, smallint, smallint, text, boolean, boolean) to service_role;

create or replace function public.register_clinic_patient(p_patient jsonb)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_patient public.patients;
    v_actor uuid := (p_patient->>'registered_by')::uuid;
    v_clinic uuid := (p_patient->>'clinic_id')::uuid;
begin
    if not exists (
        select 1 from public.user_profiles
        where id = v_actor and clinic_id = v_clinic and active = true
          and role in ('technician', 'ophthalmologist')
    ) then
        raise exception 'Active clinic staff profile required';
    end if;

    insert into public.patients (
        clinic_id, mrn, full_name, date_of_birth, gender, phone_number,
        diabetes_type, diabetes_duration_years, latest_hba1c,
        is_insulin_dependent, notes, registered_by
    ) values (
        v_clinic, p_patient->>'mrn', p_patient->>'full_name',
        (p_patient->>'date_of_birth')::date, p_patient->>'gender', p_patient->>'phone_number',
        p_patient->>'diabetes_type', nullif(p_patient->>'diabetes_duration_years', '')::integer,
        nullif(p_patient->>'latest_hba1c', '')::numeric,
        coalesce((p_patient->>'is_insulin_dependent')::boolean, false),
        p_patient->>'notes', v_actor
    ) returning * into v_patient;

    insert into public.audit_logs (clinic_id, actor_id, action, resource_type, resource_id, details)
    values (v_clinic, v_actor, 'patient.created', 'patient', v_patient.id,
            jsonb_build_object('mrn', v_patient.mrn));
    return to_jsonb(v_patient);
end;
$$;

revoke all on function public.register_clinic_patient(jsonb) from public, anon, authenticated;
grant execute on function public.register_clinic_patient(jsonb) to service_role;

create or replace function public.create_screening_records(p_screening jsonb, p_image jsonb)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_screening public.screenings;
    v_image public.retinal_images;
    v_clinic uuid := (p_screening->>'clinic_id')::uuid;
    v_patient uuid := (p_screening->>'patient_id')::uuid;
    v_actor uuid := (p_screening->>'technician_id')::uuid;
begin
    if not exists (select 1 from public.patients where id = v_patient and clinic_id = v_clinic) then
        raise exception 'Patient not found in clinic';
    end if;
    if not exists (
        select 1 from public.user_profiles
        where id = v_actor and clinic_id = v_clinic and active = true
          and role in ('technician', 'ophthalmologist')
    ) then
        raise exception 'Active clinic staff profile required';
    end if;

    insert into public.screenings (id, clinic_id, patient_id, technician_id, status)
    values ((p_screening->>'id')::uuid, v_clinic, v_patient, v_actor, 'pending_review')
    returning * into v_screening;

    insert into public.retinal_images (
        id, clinic_id, screening_id, eye, storage_path, is_gradable,
        blur_score, illumination, qc_confidence
    ) values (
        (p_image->>'id')::uuid, v_clinic, v_screening.id, p_image->>'eye',
        p_image->>'storage_path', (p_image->>'is_gradable')::boolean,
        (p_image->>'blur_score')::double precision, p_image->>'illumination',
        (p_image->>'qc_confidence')::double precision
    ) returning * into v_image;

    insert into public.audit_logs (clinic_id, actor_id, action, resource_type, resource_id, details)
    values (v_clinic, v_actor, 'screening.created', 'screening', v_screening.id,
            jsonb_build_object('retinal_image_id', v_image.id, 'eye', v_image.eye));
    return jsonb_build_object('screening_id', v_screening.id, 'retinal_image_id', v_image.id);
end;
$$;

revoke all on function public.create_screening_records(jsonb, jsonb) from public, anon, authenticated;
grant execute on function public.create_screening_records(jsonb, jsonb) to service_role;

create or replace function public.write_screening_prediction(p_prediction jsonb)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_prediction public.predictions;
    v_clinic uuid := (p_prediction->>'clinic_id')::uuid;
    v_image uuid := (p_prediction->>'retinal_image_id')::uuid;
    v_actor uuid := (p_prediction->>'requested_by')::uuid;
begin
    if not exists (select 1 from public.retinal_images where id = v_image and clinic_id = v_clinic) then
        raise exception 'Image not found in clinic';
    end if;
    if not exists (
        select 1 from public.user_profiles
        where id = v_actor and clinic_id = v_clinic and active = true
          and role in ('technician', 'ophthalmologist')
    ) then
        raise exception 'Active clinic staff profile required';
    end if;

    insert into public.predictions (
        clinic_id, retinal_image_id, predicted_grade, severity_label,
        confidence_score, inference_time_ms, probabilities,
        gradcam_heatmap_path, is_referral_recommended, requested_by
    ) values (
        v_clinic, v_image, (p_prediction->>'predicted_grade')::smallint,
        p_prediction->>'severity_label', (p_prediction->>'confidence_score')::double precision,
        (p_prediction->>'inference_time_ms')::double precision, p_prediction->'probabilities',
        p_prediction->>'gradcam_heatmap_path', (p_prediction->>'is_referral_recommended')::boolean,
        v_actor
    ) returning * into v_prediction;

    insert into public.audit_logs (clinic_id, actor_id, action, resource_type, resource_id, details)
    values (v_clinic, v_actor, 'prediction.created', 'prediction', v_prediction.id,
            jsonb_build_object('retinal_image_id', v_image, 'grade', v_prediction.predicted_grade,
                               'inference_time_ms', v_prediction.inference_time_ms));
    return to_jsonb(v_prediction);
end;
$$;

revoke all on function public.write_screening_prediction(jsonb) from public, anon, authenticated;
grant execute on function public.write_screening_prediction(jsonb) to service_role;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values
    ('fundus-images', 'fundus-images', false, 15728640, array['image/jpeg', 'image/png']),
    ('gradcam-heatmaps', 'gradcam-heatmaps', false, 10485760, array['image/png']),
    ('clinical-reports', 'clinical-reports', false, 10485760, array['application/pdf'])
on conflict (id) do update set public = false;

-- No authenticated-client storage policies are created. The backend service role
-- performs uploads and returns short-lived signed URLs for authorized media reads.
