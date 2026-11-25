// Execute real PostgreSQL SQL in an isolated in-memory PGlite instance.
import { PGlite } from '@electric-sql/pglite';
import fs from 'node:fs';
import assert from 'node:assert/strict';
const db = new PGlite();
let checks = 0;
const ok = (value) => { assert.ok(value); checks++; };
async function denied(sql, params = [], code) {
  try { await db.query(sql, params); assert.fail('Expected SQL rejection'); }
  catch (error) { if (code) assert.equal(error.code, code); else assert.ok(error.code); checks++; }
}
const bootstrap = `
create role anon; create role authenticated; create role service_role bypassrls;
create schema auth; create schema storage;
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid $$;
grant usage on schema public,auth,storage to anon,authenticated,service_role;
grant execute on function auth.uid() to authenticated,service_role;
create table storage.buckets(id text primary key,name text,public boolean);
create table storage.objects(id uuid primary key default gen_random_uuid(),bucket_id text);
alter table storage.objects enable row level security;
`;
await db.exec(bootstrap);
const migration = fs.readFileSync('supabase/migrations/202611130001_normalized_backend.sql','utf8');
// Also apply additively to the original normalized table shape with an existing row.
const existing = new PGlite();
await existing.exec(bootstrap);
await existing.exec(migration.split('-- Structured intake')[0] + 'commit;');
await existing.exec("insert into clinics(id,clinic_name) values('00000000-0000-0000-0000-000000009999','Existing clinic'); insert into patients(patient_code,full_name,clinic_id) values('PRESERVE','Existing synthetic row','00000000-0000-0000-0000-000000009999');");
await existing.exec(migration); checks++;
ok((await existing.query("select full_name from patients where patient_code='PRESERVE'")).rows[0].full_name === 'Existing synthetic row');
ok((await existing.query("select diabetes_type from patients where patient_code='PRESERVE'")).rows[0].diabetes_type === null);
await existing.close();
await db.exec(migration); checks++;
await db.exec(migration); checks++;
const id = (n) => `00000000-0000-0000-0000-${String(n).padStart(12,'0')}`;
await db.query(`insert into clinics(id,clinic_name) values($1,'Clinic A'),($2,'Clinic B')`,[id(1),id(2)]);
for (const [n,role,clinic] of [[10,'technician',1],[11,'ophthalmologist',1],[12,'administrator',1],[20,'technician',2]]) {
 await db.query('insert into user_profiles(id,full_name,role,clinic_id) values($1,$2,$3,$4)',[id(n),'Synthetic staff',role,id(clinic)]);
}
await db.exec('set role service_role');
const intake = {clinic_id:id(1),registered_by:id(10),mrn:'TEST-001',full_name:'Synthetic Patient',date_of_birth:'1980-01-01',gender:'female',diabetes_type:'type_2',diabetes_duration_years:12,latest_hba1c:7.2,is_insulin_dependent:true,notes:'Test only'};
async function register(p) { return (await db.query('select register_clinic_patient($1::jsonb) as data',[JSON.stringify(p)])).rows[0].data; }
const patient = await register(intake);
ok(patient.diabetes_duration_years===12 && patient.is_insulin_dependent && patient.mrn==='TEST-001');
await denied('select register_clinic_patient($1::jsonb)',[JSON.stringify(intake)],'23505');
await denied('select register_clinic_patient($1::jsonb)',[JSON.stringify({...intake,clinic_id:id(2),mrn:'TEST-002'})],'42501');
const otherPatient = await register({...intake,clinic_id:id(2),registered_by:id(20)});
const screen = {id:id(30),clinic_id:id(1),patient_id:patient.id,technician_id:id(10)};
const image = {id:id(31),eye:'OD',storage_path:`${id(1)}/${id(31)}.png`,is_gradable:true,blur_score:120,illumination:'optimal',qc_confidence:.9,mime_type:'image/png',file_size_bytes:3000,image_width:640,image_height:480};
await denied('select create_screening_records($1::jsonb,$2::jsonb)',[JSON.stringify({...screen,patient_id:otherPatient.id}),JSON.stringify(image)],'P0002');
await db.query('select create_screening_records($1::jsonb,$2::jsonb)',[JSON.stringify(screen),JSON.stringify(image)]); checks++;
ok((await db.query('select image_width from retinal_images where id=$1',[id(31)])).rows[0].image_width===640);
const prediction={clinic_id:id(1),requested_by:id(10),retinal_image_id:id(31),predicted_grade:2,confidence_score:.8,probabilities:[.05,.05,.8,.05,.05],is_referral_recommended:true,inference_time_ms:100,gradcam_heatmap_path:`${id(1)}/${id(31)}.png`};
await denied('select write_screening_prediction($1::jsonb)',[JSON.stringify({...prediction,probabilities:[1,0]})],'23514');
const pred=(await db.query('select write_screening_prediction($1::jsonb) as data',[JSON.stringify(prediction)])).rows[0].data;
ok(pred.predicted_grade===2);
ok(Number((await db.query('select count(*) as n from prediction_probabilities where prediction_id=$1',[pred.id])).rows[0].n)===5);
ok(Number((await db.query('select count(*) as n from explanations where prediction_id=$1',[pred.id])).rows[0].n)===1);
const reviewSql='select write_screening_review($1::uuid,$2::uuid,$3::uuid,$4::smallint,$5::smallint,$6::text,$7::boolean,$8::boolean) as data';
const args=[id(30),id(1),id(11),2,3,'Escaped <clinical> notes',true,false];
await denied(reviewSql,[...args.slice(0,2),id(10),...args.slice(3)],'42501');
await denied(reviewSql,[id(30),id(2),id(20),...args.slice(3)],'42501');
const draft=(await db.query(reviewSql,args)).rows[0].data;
ok(draft.overall_grade===2 && draft.grade_override===3 && draft.is_urgent_referral && !draft.is_signed_off);
const signedArgs=[...args.slice(0,7),true];
const signed=(await db.query(reviewSql,signedArgs)).rows[0].data;
ok(signed.is_signed_off && signed.signed_off_at);
ok((await db.query(reviewSql,signedArgs)).rows[0].data.id===signed.id);
await denied(reviewSql,[...signedArgs.slice(0,3),4,...signedArgs.slice(4)],'55000');
await denied('delete from audit_logs',[],'42501');
// Failure of the audit insert must roll back the clinical write in the same RPC.
await db.exec(`reset role; create function reject_test_audit() returns trigger language plpgsql as $$ begin raise exception 'test audit failure'; end $$;
create trigger reject_test_audit before insert on audit_logs for each row execute function reject_test_audit(); set role service_role;`);
await denied('select register_clinic_patient($1::jsonb)',[JSON.stringify({...intake,mrn:'ROLLBACK-001'})],'P0001');
ok((await db.query("select id from patients where patient_code='ROLLBACK-001'")).rows.length===0);
await db.exec('reset role; drop trigger reject_test_audit on audit_logs;');
// A permissive legacy policy must not defeat the restrictive clinic boundary.
await db.exec('create policy legacy_allow_all on patients for select to authenticated using(true); set role authenticated;');
await db.query("select set_config('request.jwt.claim.sub',$1,false)",[id(10)]);
ok((await db.query('select id from patients')).rows.length===1);
ok((await db.query('select id from user_profiles')).rows.length===1);
for (const table of ['screenings','retinal_images','predictions','prediction_probabilities','explanations','reports']) {
 ok((await db.query(`select id from ${table}`)).rows.length>0);
}
await denied('select register_clinic_patient($1::jsonb)',[JSON.stringify({...intake,mrn:'FORBIDDEN'})],'42501');
await denied("update user_profiles set role='administrator'",[],'42501');
await db.query("select set_config('request.jwt.claim.sub',$1,false)",[id(20)]);
ok((await db.query('select id from patients')).rows.length===1);
for (const table of ['screenings','retinal_images','predictions','prediction_probabilities','explanations','reports','audit_logs']) {
 ok((await db.query(`select id from ${table}`)).rows.length===(table==='audit_logs'?1:0));
}
await db.exec('reset role; set role anon;');
await denied('select * from patients',[],'42501');
await db.exec('reset role;');
ok((await db.query("select relrowsecurity from pg_class where oid='reports'::regclass")).rows[0].relrowsecurity);
await db.exec('set role service_role');
await db.query('select netrava_require_staff($1,$2,true)',[id(12),id(1)]); checks++;
await db.exec('reset role');
await db.query('update user_profiles set is_active=false where id=$1',[id(10)]);
await db.exec('set role service_role');
await denied('select register_clinic_patient($1::jsonb)',[JSON.stringify({...intake,mrn:'INACTIVE'})],'42501');
await db.exec('reset role; set role authenticated');
await db.query("select set_config('request.jwt.claim.sub',$1,false)",[id(10)]);
ok((await db.query('select id from patients')).rows.length===0);
await db.exec('reset role');
await db.query('update user_profiles set is_active=true where id=$1',[id(10)]);
await db.query('update clinics set is_active=false where id=$1',[id(1)]);
await db.exec('set role service_role');
await denied('select register_clinic_patient($1::jsonb)',[JSON.stringify({...intake,mrn:'INACTIVE-CLINIC'})],'42501');
await db.exec('reset role');
await db.query('update clinics set is_active=true where id=$1',[id(1)]);
await db.exec(`grant select on storage.objects to anon,authenticated;
create policy legacy_storage_allow on storage.objects for select to anon,authenticated using(true);
insert into storage.objects(bucket_id) values('fundus-images'),('gradcam-heatmaps'),('clinical-reports'),('other-public');
set role authenticated;`);
ok((await db.query('select bucket_id from storage.objects')).rows.length===1);
await db.exec('reset role; set role anon');
ok((await db.query('select bucket_id from storage.objects')).rows.length===1);
await db.exec('reset role');
console.log(JSON.stringify({engine:'PGlite PostgreSQL',checks,passed:checks,failed:0}));
if (process.argv.includes('--stdio')) {
 const {createInterface}=await import('node:readline');
 const input=createInterface({input:process.stdin,terminal:false});
 for await(const line of input){
  try {const {sql,params=[]}=JSON.parse(line);console.log(JSON.stringify(await db.query(sql,params)));}
  catch(e){console.log(JSON.stringify({error:{code:e.code,message:'Test SQL operation failed'}}));}
 }
 await db.close();
} else await db.close();
