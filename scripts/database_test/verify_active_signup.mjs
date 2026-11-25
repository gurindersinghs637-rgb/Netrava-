import { PGlite } from '@electric-sql/pglite';
import fs from 'node:fs';
import assert from 'node:assert/strict';
const db = new PGlite();
await db.exec(`create role anon; create role authenticated; create role service_role bypassrls;
create schema auth; create schema storage;
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid $$;
create table auth.users(id uuid primary key, email text, raw_user_meta_data jsonb);
create table storage.buckets(id text primary key,name text,public boolean);
create table storage.objects(id uuid primary key default gen_random_uuid(),bucket_id text);
grant usage on schema public,auth,storage to authenticated,service_role;`);
for (const file of ['202611130001_normalized_backend.sql','202611140001_public_signup.sql','202611140002_active_signup.sql','202611140002_active_signup.sql']) {
 await db.exec(fs.readFileSync('supabase/migrations/'+file,'utf8'));
}
const id = n => `00000000-0000-0000-0000-${String(n).padStart(12,'0')}`;
// Match the hosted schema: duplicate constant workspace names must fail.
await db.exec('alter table clinics add constraint clinics_clinic_name_key unique (clinic_name)');
const signup = async n => db.query('insert into auth.users values($1,$2,$3)',[id(n),`new${n}@example.com`,JSON.stringify({full_name:`Person ${n}`,phone:'+919876543210',role:'administrator',clinic_id:id(99),is_active:false})]);
await signup(1);
const originalProfile = (await db.query('select * from user_profiles where id=$1', [id(1)])).rows[0];
const originalClinic = (await db.query('select * from clinics where id=$1', [originalProfile.clinic_id])).rows[0];
assert.equal(originalClinic.clinic_name, 'Personal screening workspace');
await db.exec('begin; savepoint old_constant_name');
try {
 await signup(2);
 assert.fail('Old constant workspace name must fail for the second signup');
} catch (e) {
 assert.equal(e.code, '23505');
 await db.exec('rollback to savepoint old_constant_name');
}
assert.equal((await db.query('select count(*)::int as n from auth.users')).rows[0].n, 1);
assert.equal((await db.query('select count(*)::int as n from clinics')).rows[0].n, 1);
await db.exec('release savepoint old_constant_name; commit');

for (let attempt = 0; attempt < 2; attempt++) {
 await db.exec(fs.readFileSync('supabase/migrations/202611150001_unique_signup_workspace.sql', 'utf8'));
}
assert.deepEqual((await db.query('select * from user_profiles where id=$1', [id(1)])).rows[0], originalProfile);
assert.deepEqual((await db.query('select * from clinics where id=$1', [originalProfile.clinic_id])).rows[0], originalClinic);
// These UUIDs share their entire prefix; shortened UUID workspace suffixes collide.
for (const n of [2,3]) await signup(n);
const newClinics = (await db.query('select c.clinic_name, p.id from clinics c join user_profiles p on p.clinic_id=c.id where p.id<>$1 order by p.id', [id(1)])).rows;
assert.equal(newClinics.length, 2);
for (const c of newClinics) assert.equal(c.clinic_name, `Personal screening workspace - ${c.id}`);
assert.equal(new Set(newClinics.map(c => c.clinic_name)).size, 2);
const profiles=(await db.query('select * from user_profiles order by id')).rows;
assert.equal(profiles.length,3);
for (const p of profiles) {assert.equal(p.role,'technician');assert.equal(p.is_active,true);assert.equal(p.phone,'+919876543210');assert.ok(p.created_at);assert.ok(p.clinic_id);}
assert.notEqual(profiles[0].clinic_id,profiles[1].clinic_id);
await db.query('select set_config($1,$2,false)',['request.jwt.claim.sub',id(1)]);
await db.exec('set role authenticated');
assert.equal((await db.query('select * from clinics')).rows.length,1);
assert.equal((await db.query('select * from user_profiles')).rows.length,1);
try {await db.exec("update user_profiles set role='administrator'");assert.fail('Expected denied update');} catch(e) {assert.equal(e.code,'42501');}
await db.exec('reset role; set role service_role');
const patient={clinic_id:profiles[0].clinic_id,registered_by:id(1),mrn:'NEW-001',full_name:'Local test patient',date_of_birth:'1980-01-01',gender:'female'};
const result=(await db.query('select register_clinic_patient($1::jsonb) as data',[JSON.stringify(patient)])).rows[0].data;
assert.ok(result.id);
try {await db.query('select register_clinic_patient($1::jsonb)',[JSON.stringify({...patient,clinic_id:profiles[1].clinic_id})]);assert.fail('Expected denied cross-clinic');} catch(e) {assert.equal(e.code,'42501');}
await db.exec('reset role');
await db.exec("alter table user_profiles add constraint reject_test_name check(full_name <> 'Reject Me')");
const before=(await db.query('select count(*)::int as n from clinics')).rows[0].n;
try {await db.query('insert into auth.users values($1,$2,$3)',[id(4),'rollback@example.com','{"full_name":"Reject Me"}']);assert.fail('Expected rollback');} catch(e) {assert.equal(e.code,'23514');}
assert.equal((await db.query('select count(*)::int as n from clinics')).rows[0].n,before);
assert.equal((await db.query('select count(*)::int as n from auth.users')).rows[0].n,3);
assert.equal((await db.query('select count(*)::int as n from user_profiles')).rows[0].n,3);
assert.equal((await db.query('select id from auth.users where id=$1', [id(4)])).rows.length,0);
console.log('Active signup SQL passed: hosted-equivalent UNIQUE constraint reproduces old second-signup 23505; repeatable full-UUID workspace fix; existing data preserved; persistence, isolated workspaces, RLS, role protection, patient creation, cross-clinic denial, atomic rollback.');
await db.close();
