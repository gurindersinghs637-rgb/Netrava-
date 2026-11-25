# NETRAVA normalized database

The supported migration is `migrations/202611130001_normalized_backend.sql`.
It creates a normalized schema in an empty Supabase project, or adds the missing
backend fields/functions to the normalized tables observed in the existing project.
The metadata-only observation is saved in `schema_rest_snapshot.json`; it contains
no records, credentials, policies or function bodies.

The conflicting, unapplied original migration is preserved under `legacy/` for
history. Do not execute that file or combine its schema with this migration.

## Apply to the development project

Open the intended Supabase project's SQL Editor and run the complete supported
migration in one execution. It is transactional and repeatable. Existing clinical
rows are preserved. Added unique indexes deliberately fail if duplicate patient
codes, screening reports or class-probability rows already exist; investigate any
such error instead of deleting records or bypassing the constraint. A public
medical bucket also causes rollback instead of silently changing its visibility.

The migration adds all four service-only transactional RPCs, structured diabetes
intake, image QC/size/hash metadata, complete report fields, restrictive clinic
RLS, backend-only medical-media policies, and append-only audit enforcement.
Existing permissive read policies cannot defeat the new restrictive clinic bound.
Authenticated clients get SELECT only; writes go through the backend. The helper
`rls_auto_enable`, if present, loses client execute permission.

The SQL was executed twice in isolated PGlite PostgreSQL and exercised through
the backend with real inference. The hosted database has not been migrated.
PostgREST metadata does not expose its existing check constraints or triggers;
deployment on that specific database must still pass before readiness is claimed.
No direct SQL connection or database-management connector is available in this
workspace, so a service-role REST key cannot apply DDL.

## Local verification

Run from the repository root (Node and Python 3.11 required):

```powershell
npm.cmd ci --prefix scripts/database_test --no-audit --no-fund
node scripts/database_test/verify.mjs
.\.venv\Scripts\python.exe scripts/database_test/verify_api_workflow.py
```

The first check uses actual PostgreSQL functions/RLS and synthetic records. The
second runs FastAPI, actual PostgreSQL RPCs, the real checkpoint and PDF generation.
Its identity/object-storage adapters are controlled locally; it does not test live
GoTrue or Supabase Storage. All test data lives in an in-memory database.

After deployment, follow the single live verification procedure in
`docs/FINAL_BACKEND_READINESS_REPORT.md`. Never paste credentials or tokens into chat.
