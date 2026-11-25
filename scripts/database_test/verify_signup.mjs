import { PGlite } from '@electric-sql/pglite';
import fs from 'node:fs';
import assert from 'node:assert/strict';
const db = new PGlite();
await db.exec(`create role anon; create role authenticated; create schema auth;
create table auth.users(id uuid primary key, email text, raw_user_meta_data jsonb);
create table public.user_profiles(id uuid primary key, full_name text not null, role text not null,
clinic_id uuid, is_active boolean not null, created_at timestamptz default now());`);
const sql = fs.readFileSync('supabase/migrations/202611140001_public_signup.sql','utf8');
await db.exec(sql); await db.exec(sql);
const id='00000000-0000-0000-0000-000000000111';
await db.query(`insert into auth.users values($1,'new@example.com',$2)`,[id,JSON.stringify({full_name:'New Person',role:'administrator',clinic_id:id,is_active:true})]);
const p=(await db.query('select * from public.user_profiles')).rows[0];
assert.equal(p.id,id); assert.equal(p.full_name,'New Person'); assert.equal(p.role,'technician');
assert.equal(p.is_active,false); assert.equal(p.clinic_id,null); assert.ok(p.created_at);
await db.exec(`alter table public.user_profiles add constraint reject_test_name check(full_name <> 'Reject Me')`);
try {
 await db.query(`insert into auth.users values('00000000-0000-0000-0000-000000000112','rollback@example.com','{"full_name":"Reject Me"}')`);
 assert.fail('Expected rollback');
} catch(e) { assert.equal(e.code,'23514'); }
assert.equal((await db.query('select count(*)::int as n from auth.users')).rows[0].n,1);
console.log('Signup PostgreSQL checks passed: repeatable migration, safe role/status/clinic, persisted profile, atomic rollback.');
await db.close();
