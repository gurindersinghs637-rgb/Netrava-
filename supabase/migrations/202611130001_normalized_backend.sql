-- Standalone normalized-schema reconciliation. Do NOT run the legacy 202611030001 migration first.

-- Apply in a reviewed development project. Entire migration is atomic and repeatable.

begin;

create table if not exists public.clinics (
    id uuid primary key not null default gen_random_uuid(),
    clinic_name text not null,
    address text,
    phone text,
    email text,
    is_active boolean not null default true,
    created_at timestamp with time zone not null default now()
);

create table if not exists public.user_profiles (
    id uuid primary key not null,
    full_name text not null,
    role text not null,
    clinic_id uuid references public.clinics(id),
    phone text,
    is_active boolean not null default true,
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now()
);

create table if not exists public.patients (
    id uuid primary key not null default gen_random_uuid(),
    patient_code text not null,
    full_name text not null,
    date_of_birth date,
    sex text,
    phone text,
    email text,
    medical_notes text,
    clinic_id uuid references public.clinics(id),
    created_by uuid,
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now()
);

create table if not exists public.screenings (
    id uuid primary key not null default gen_random_uuid(),
    patient_id uuid not null references public.patients(id),
    technician_id uuid,
    clinic_id uuid references public.clinics(id),
    screening_date timestamp with time zone not null default now(),
    status text not null default 'pending',
    notes text,
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now()
);

create table if not exists public.retinal_images (
    id uuid primary key not null default gen_random_uuid(),
    screening_id uuid not null references public.screenings(id),
    eye_side text not null,
    storage_bucket text not null default 'fundus-images',
    storage_path text not null,
    original_filename text,
    mime_type text,
    file_size_bytes bigint,
    image_width integer,
    image_height integer,
    uploaded_by uuid,
    uploaded_at timestamp with time zone not null default now()
);

create table if not exists public.predictions (
    id uuid primary key not null default gen_random_uuid(),
    retinal_image_id uuid not null references public.retinal_images(id),
    model_name text not null default 'EfficientNet-B3',
    model_version text,
    predicted_grade integer not null,
    confidence numeric not null,
    referral_recommended boolean not null,
    inference_time_ms numeric,
    created_at timestamp with time zone not null default now()
);

create table if not exists public.prediction_probabilities (
    id uuid primary key not null default gen_random_uuid(),
    prediction_id uuid not null references public.predictions(id),
    dr_grade integer not null,
    probability numeric not null
);

create table if not exists public.explanations (
    id uuid primary key not null default gen_random_uuid(),
    prediction_id uuid not null references public.predictions(id),
    explanation_type text not null default 'Grad-CAM',
    storage_bucket text not null default 'gradcam-heatmaps',
    storage_path text not null,
    target_layer text,
    created_at timestamp with time zone not null default now()
);

create table if not exists public.reports (
    id uuid primary key not null default gen_random_uuid(),
    screening_id uuid not null references public.screenings(id),
    prediction_id uuid references public.predictions(id),
    reviewer_id uuid,
    ai_summary text,
    clinical_assessment text,
    final_grade integer,
    review_status text not null default 'pending',
    storage_bucket text default 'clinical-reports',
    storage_path text,
    reviewed_at timestamp with time zone,
    created_at timestamp with time zone not null default now()
);

create table if not exists public.audit_logs (
    id uuid primary key not null default gen_random_uuid(),
    user_id uuid,
    action text not null,
    table_name text,
    record_id uuid,
    details jsonb not null,
    created_at timestamp with time zone not null default now()
);

-- Structured intake and complete report semantics; existing values are preserved.
alter table public.patients add column if not exists diabetes_type text check (diabetes_type in ('type_1','type_2','gestational','other'));
alter table public.patients add column if not exists diabetes_duration_years integer check (diabetes_duration_years between 0 and 100);
alter table public.patients add column if not exists latest_hba1c numeric check (latest_hba1c between 3 and 20);
alter table public.patients add column if not exists is_insulin_dependent boolean not null default false;
alter table public.retinal_images add column if not exists content_sha256 text check (content_sha256 ~ '^[0-9a-f]{64}$');
alter table public.retinal_images add column if not exists is_gradable boolean;
alter table public.retinal_images add column if not exists blur_score double precision;
alter table public.retinal_images add column if not exists illumination text;
alter table public.retinal_images add column if not exists qc_confidence double precision;
alter table public.reports add column if not exists overall_grade smallint check (overall_grade between 0 and 4);
alter table public.reports add column if not exists grade_override smallint check (grade_override between 0 and 4);
-- NULL on historical records means unknown, never a fabricated false value.
alter table public.reports add column if not exists is_urgent_referral boolean;
alter table public.reports add column if not exists updated_at timestamptz not null default now();
alter table public.audit_logs add column if not exists clinic_id uuid references public.clinics(id);
create unique index if not exists netrava_patient_code_unique on public.patients(clinic_id,patient_code);
create unique index if not exists netrava_report_screening_unique on public.reports(screening_id);
create unique index if not exists netrava_probability_unique on public.prediction_probabilities(prediction_id,dr_grade);
create index if not exists netrava_patient_clinic on public.patients(clinic_id,created_at desc);
create index if not exists netrava_screening_clinic on public.screenings(clinic_id,created_at desc);
create index if not exists netrava_image_screening on public.retinal_images(screening_id);
create index if not exists netrava_prediction_image on public.predictions(retinal_image_id,created_at desc);
create index if not exists netrava_explanation_prediction on public.explanations(prediction_id);

create or replace function public.netrava_require_staff(p_actor uuid,p_clinic uuid,p_review boolean default false)
returns void language plpgsql set search_path = public, pg_temp as $$
begin
 if not exists(select 1 from public.user_profiles p join public.clinics c on c.id=p.clinic_id
  where p.id=p_actor and p.clinic_id=p_clinic and p.is_active and c.is_active
  and (p.role in ('ophthalmologist','administrator') or (not p_review and p.role='technician'))) then
  raise exception using errcode='42501',message='Active authorized clinic staff required';
 end if;
end $$;

create or replace function public.register_clinic_patient(p_patient jsonb)
returns jsonb language plpgsql set search_path = public, pg_temp as $$
declare v public.patients; actor uuid:=(p_patient->>'registered_by')::uuid; clinic uuid:=(p_patient->>'clinic_id')::uuid;
begin
 perform public.netrava_require_staff(actor,clinic);
 if length(trim(p_patient->>'full_name')) not between 2 and 200
 or (p_patient->>'date_of_birth')::date > current_date
 or p_patient->>'gender' not in ('male','female','other')
 or p_patient->>'mrn' !~ '^[A-Za-z0-9_-]{3,50}$'
 or p_patient->>'diabetes_type' not in ('type_1','type_2','gestational','other') then
  raise exception using errcode='23514',message='Invalid patient intake';
 end if;
 insert into public.patients(patient_code,full_name,date_of_birth,sex,phone,medical_notes,clinic_id,created_by,
 diabetes_type,diabetes_duration_years,latest_hba1c,is_insulin_dependent)
 values(upper(p_patient->>'mrn'),trim(p_patient->>'full_name'),(p_patient->>'date_of_birth')::date,p_patient->>'gender',
 p_patient->>'phone_number',p_patient->>'notes',clinic,actor,p_patient->>'diabetes_type',
 (p_patient->>'diabetes_duration_years')::integer,(p_patient->>'latest_hba1c')::numeric,
 coalesce((p_patient->>'is_insulin_dependent')::boolean,false)) returning * into v;
 insert into public.audit_logs(user_id,clinic_id,action,table_name,record_id,details)
 values(actor,clinic,'patient.created','patients',v.id,'{}');
 return to_jsonb(v)||jsonb_build_object('mrn',v.patient_code,'registered_by',v.created_by);
end $$;

create or replace function public.create_screening_records(p_screening jsonb,p_image jsonb)
returns jsonb language plpgsql set search_path = public, pg_temp as $$
declare sid uuid:=(p_screening->>'id')::uuid; iid uuid:=(p_image->>'id')::uuid;
 clinic uuid:=(p_screening->>'clinic_id')::uuid; actor uuid:=(p_screening->>'technician_id')::uuid;
begin
 perform public.netrava_require_staff(actor,clinic);
 if not exists(select 1 from public.patients where id=(p_screening->>'patient_id')::uuid and clinic_id=clinic) then
  raise exception using errcode='P0002',message='Patient not found in clinic';
 end if;
 if p_image->>'eye' not in ('OD','OS') or (p_image->>'is_gradable')::boolean is not true
 or split_part(p_image->>'storage_path','/',1) is distinct from clinic::text then
  raise exception using errcode='23514',message='Invalid image metadata';
 end if;
 insert into public.screenings(id,patient_id,technician_id,clinic_id,status)
 values(sid,(p_screening->>'patient_id')::uuid,actor,clinic,'pending');
 insert into public.retinal_images(id,screening_id,eye_side,storage_path,uploaded_by,mime_type,file_size_bytes,image_width,image_height,
 is_gradable,blur_score,illumination,qc_confidence,content_sha256)
 values(iid,sid,case when p_image->>'eye'='OD' then 'right' else 'left' end,p_image->>'storage_path',actor,
 p_image->>'mime_type',(p_image->>'file_size_bytes')::bigint,(p_image->>'image_width')::integer,(p_image->>'image_height')::integer,
 true,(p_image->>'blur_score')::double precision,p_image->>'illumination',(p_image->>'qc_confidence')::double precision,p_image->>'content_sha256');
 insert into public.audit_logs(user_id,clinic_id,action,table_name,record_id,details)
 values(actor,clinic,'screening.created','screenings',sid,jsonb_build_object('retinal_image_id',iid));
 return jsonb_build_object('screening_id',sid,'retinal_image_id',iid);
end $$;

create or replace function public.write_screening_prediction(p_prediction jsonb)
returns jsonb language plpgsql set search_path = public, pg_temp as $$
declare v public.predictions; clinic uuid:=(p_prediction->>'clinic_id')::uuid;
 actor uuid:=(p_prediction->>'requested_by')::uuid; image_id uuid:=(p_prediction->>'retinal_image_id')::uuid;
 probs jsonb:=p_prediction->'probabilities'; total numeric; grade integer:=(p_prediction->>'predicted_grade')::integer;
begin
 perform public.netrava_require_staff(actor,clinic);
 if not exists(select 1 from public.retinal_images i join public.screenings s on s.id=i.screening_id where i.id=image_id and s.clinic_id=clinic) then
  raise exception using errcode='P0002',message='Image not found in clinic';
 end if;
 if jsonb_typeof(probs) is distinct from 'array' then raise exception using errcode='23514',message='Invalid probabilities'; end if;
 if jsonb_array_length(probs)<>5 or grade not between 0 and 4
 or exists(select 1 from jsonb_array_elements_text(probs) x where x::numeric not between 0 and 1) then
  raise exception using errcode='23514',message='Invalid probabilities or grade';
 end if;
 select sum(x::numeric) into total from jsonb_array_elements_text(probs) x;
 if abs(total-1)>0.001 or total is null
 or abs((p_prediction->>'confidence_score')::numeric-(probs->>grade)::numeric)>0.001
 or (p_prediction->>'is_referral_recommended')::boolean is distinct from (grade>=2) then
  raise exception using errcode='23514',message='Inconsistent prediction';
 end if;
 insert into public.predictions(retinal_image_id,model_name,model_version,predicted_grade,confidence,referral_recommended,inference_time_ms)
 values(image_id,'EfficientNet-B3','1.0.0',grade,(p_prediction->>'confidence_score')::numeric,grade>=2,(p_prediction->>'inference_time_ms')::numeric)
 returning * into v;
 insert into public.prediction_probabilities(prediction_id,dr_grade,probability)
 select v.id,ordinality-1,value::numeric from jsonb_array_elements_text(probs) with ordinality;
 if nullif(p_prediction->>'gradcam_heatmap_path','') is not null then
  if split_part(p_prediction->>'gradcam_heatmap_path','/',1) is distinct from clinic::text then
   raise exception using errcode='23514',message='Invalid heatmap path';
  end if;
  insert into public.explanations(prediction_id,explanation_type,storage_bucket,storage_path,target_layer)
  values(v.id,'Grad-CAM','gradcam-heatmaps',p_prediction->>'gradcam_heatmap_path','conv_head');
 end if;
 insert into public.audit_logs(user_id,clinic_id,action,table_name,record_id,details)
 values(actor,clinic,'prediction.created','predictions',v.id,jsonb_build_object('grade',grade));
 return to_jsonb(v);
end $$;

create or replace function public.netrava_report_json(p public.reports)
returns jsonb language sql immutable set search_path = public, pg_temp as $$
 select jsonb_build_object('id',p.id,'screening_id',p.screening_id,'prediction_id',p.prediction_id,
 'overall_grade',p.overall_grade,'grade_override',p.grade_override,'ophthalmologist_notes',p.clinical_assessment,
 'is_urgent_referral',p.is_urgent_referral,'is_signed_off',p.review_status='approved','signed_off_at',p.reviewed_at,
 'created_at',p.created_at,'updated_at',p.updated_at)
$$;

create or replace function public.write_screening_review(p_screening_id uuid,p_clinic_id uuid,p_ophthalmologist_id uuid,
 p_overall_grade smallint,p_grade_override smallint,p_ophthalmologist_notes text,p_is_urgent_referral boolean,p_is_signed_off boolean)
returns jsonb language plpgsql set search_path = public, pg_temp as $$
declare v public.reports; prediction uuid;
begin
 perform public.netrava_require_staff(p_ophthalmologist_id,p_clinic_id,true);
 -- Serialize both first-insert and subsequent reviews; signed reports are immutable.
 perform 1 from public.screenings where id=p_screening_id and clinic_id=p_clinic_id for update;
 if not found then raise exception using errcode='P0002',message='Screening not found in clinic'; end if;
 select * into v from public.reports where screening_id=p_screening_id for update;
 if found and v.review_status='approved' then
  if v.reviewer_id=p_ophthalmologist_id and v.overall_grade=p_overall_grade
  and v.grade_override is not distinct from p_grade_override
  and v.clinical_assessment is not distinct from p_ophthalmologist_notes
  and v.is_urgent_referral=p_is_urgent_referral and p_is_signed_off then return public.netrava_report_json(v); end if;
  raise exception using errcode='55000',message='Signed report is immutable';
 end if;
 if p_overall_grade not between 0 and 4 or (p_grade_override is not null and p_grade_override not between 0 and 4)
 or length(p_ophthalmologist_notes)>5000 then raise exception using errcode='23514',message='Invalid review'; end if;
 select p.id into prediction from public.predictions p join public.retinal_images i on i.id=p.retinal_image_id
 where i.screening_id=p_screening_id order by p.created_at desc,p.id desc limit 1;
 if prediction is null then raise exception using errcode='55000',message='Prediction required before review'; end if;
 insert into public.reports(screening_id,prediction_id,reviewer_id,overall_grade,grade_override,clinical_assessment,
 final_grade,is_urgent_referral,review_status,reviewed_at)
 values(p_screening_id,prediction,p_ophthalmologist_id,p_overall_grade,p_grade_override,p_ophthalmologist_notes,
 coalesce(p_grade_override,p_overall_grade),p_is_urgent_referral,case when p_is_signed_off then 'approved' else 'pending' end,
 case when p_is_signed_off then now() else null end)
 on conflict(screening_id) do update set prediction_id=excluded.prediction_id,reviewer_id=excluded.reviewer_id,
 overall_grade=excluded.overall_grade,grade_override=excluded.grade_override,clinical_assessment=excluded.clinical_assessment,
 final_grade=excluded.final_grade,is_urgent_referral=excluded.is_urgent_referral,review_status=excluded.review_status,
 reviewed_at=excluded.reviewed_at,updated_at=now() returning * into v;
 update public.screenings set status=case when p_is_signed_off then 'completed' else 'pending' end,updated_at=now() where id=p_screening_id;
 insert into public.audit_logs(user_id,clinic_id,action,table_name,record_id,details)
 values(p_ophthalmologist_id,p_clinic_id,'screening.reviewed','reports',v.id,jsonb_build_object('is_signed_off',p_is_signed_off));
 return public.netrava_report_json(v);
end $$;

-- Service-only write functions. No security definer privileges are needed for writes.
revoke all on function public.netrava_require_staff(uuid,uuid,boolean),public.register_clinic_patient(jsonb),
 public.create_screening_records(jsonb,jsonb),public.write_screening_prediction(jsonb),
 public.netrava_report_json(public.reports),public.write_screening_review(uuid,uuid,uuid,smallint,smallint,text,boolean,boolean)
 from public,anon,authenticated;
grant execute on function public.netrava_require_staff(uuid,uuid,boolean),public.register_clinic_patient(jsonb),
 public.create_screening_records(jsonb,jsonb),public.write_screening_prediction(jsonb),
 public.netrava_report_json(public.reports),public.write_screening_review(uuid,uuid,uuid,smallint,smallint,text,boolean,boolean) to service_role;

create or replace function public.netrava_current_clinic()
returns uuid language sql stable security definer set search_path = public, pg_temp as $$
 select p.clinic_id from public.user_profiles p join public.clinics c on c.id=p.clinic_id
 where p.id=auth.uid() and p.is_active and c.is_active
$$;
revoke all on function public.netrava_current_clinic() from public,anon;
grant execute on function public.netrava_current_clinic() to authenticated,service_role;

-- Restrictive policies cap any existing permissive policies at the clinic boundary.
-- Clients are read-only; all writes go through the authenticated backend.
do $policy$
declare t text; predicate text;
begin
 foreach t in array array['clinics','user_profiles','patients','screenings','retinal_images','predictions','prediction_probabilities','explanations','reports','audit_logs'] loop
  predicate:=case t
   when 'clinics' then 'id=public.netrava_current_clinic()'
   when 'retinal_images' then 'screening_id in (select id from public.screenings where clinic_id=public.netrava_current_clinic())'
   when 'predictions' then 'retinal_image_id in (select id from public.retinal_images)'
   when 'prediction_probabilities' then 'prediction_id in (select id from public.predictions)'
   when 'explanations' then 'prediction_id in (select id from public.predictions)'
   when 'reports' then 'screening_id in (select id from public.screenings where clinic_id=public.netrava_current_clinic())'
   else 'clinic_id=public.netrava_current_clinic()' end;
  execute format('alter table public.%I enable row level security',t);
  execute format('drop policy if exists netrava_read on public.%I',t);
  execute format('drop policy if exists netrava_clinic_boundary on public.%I',t);
  execute format('create policy netrava_read on public.%I for select to authenticated using (%s)',t,predicate);
  execute format('create policy netrava_clinic_boundary on public.%I as restrictive for all to authenticated using (%s) with check (false)',t,predicate);
  execute format('revoke all on public.%I from public,anon,authenticated',t);
  execute format('grant select on public.%I to authenticated',t);
  execute format('grant select,insert,update,delete on public.%I to service_role',t);
 end loop;
end $policy$;
-- Profiles must never expose other users or enable role changes through direct access.
drop policy if exists netrava_profile_self on public.user_profiles;
create policy netrava_profile_self on public.user_profiles as restrictive for select to authenticated using(id=auth.uid());

create or replace function public.netrava_audit_immutable()
returns trigger language plpgsql as $$ begin raise exception using errcode='55000',message='Audit records are append-only'; end $$;
drop trigger if exists netrava_audit_immutable on public.audit_logs;
create trigger netrava_audit_immutable before update or delete on public.audit_logs for each row execute function public.netrava_audit_immutable();
revoke update,delete,truncate on public.audit_logs from service_role;
-- The event-trigger helper must not be callable by client roles.
do $$ declare f record; begin
 for f in select oid::regprocedure as signature from pg_proc where pronamespace='public'::regnamespace and proname='rls_auto_enable' loop
  execute format('revoke execute on function %s from public,anon,authenticated',f.signature);
 end loop;
end $$;
-- Keep all existing bucket settings intact; refuse a public medical bucket.
insert into storage.buckets(id,name,public) values('fundus-images','fundus-images',false),
 ('gradcam-heatmaps','gradcam-heatmaps',false),('clinical-reports','clinical-reports',false) on conflict(id) do nothing;
do $$ begin
 if exists(select 1 from storage.buckets where id in ('fundus-images','gradcam-heatmaps','clinical-reports') and public) then
  raise exception 'Medical buckets must be private; migration rolled back';
 end if;
end $$;
-- Existing permissive storage policies cannot grant direct client medical-media access.
drop policy if exists netrava_backend_media_only on storage.objects;
create policy netrava_backend_media_only on storage.objects as restrictive for all to anon,authenticated
 using(bucket_id not in ('fundus-images','gradcam-heatmaps','clinical-reports'))
 with check(bucket_id not in ('fundus-images','gradcam-heatmaps','clinical-reports'));
notify pgrst,'reload schema';
commit;
