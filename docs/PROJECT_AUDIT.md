# NETRAVA Backend Audit

**Updated:** 2026-11-03  
**Scope:** Existing backend and AI only. Flutter source was preserved and not developed.  
**Workspace:** `C:\Users\HP\NETRAVA_1`

## Architecture and current state

- `backend/app/` contains the FastAPI app, v1 routes, Pydantic schemas, security/configuration, API services, image validation, and the ML bridge.
- `ai_model/inference/` contains the EfficientNet-B3 loader, preprocessing, predictor, and Grad-CAM implementation. The checkpoint is `ai_model/checkpoint/best_efficientnet_b3_staged.pth`.
- `supabase/migrations/202611030001_backend_core.sql` defines clinics, profiles, patients, screenings, retinal images, predictions, reports, audit records, RLS, private buckets, and transactional write RPCs.
- `shared/api_contracts/openapi_contract.json` is generated from FastAPI routes.
- `frontend/flutter_app/` remains an unconnected welcome/login prototype. No frontend implementation work was done in this backend task.

## Verified locally

- Python 3.11 interpreter used: `C:\Users\HP\.conda\envs\py311\python.exe` (the path shown in the request had a missing slash before `.conda`).
- FastAPI imports from the repository root and Uvicorn starts. The checkpoint loads during application startup; the server reported `model_loaded: true`.
- On port 8003, `/api/v1/docs` and `/api/v1/openapi.json` returned 200. Missing-token access to protected routes returned 401. Login without Supabase configuration returned 503. Health stayed responsive and reported `degraded`, `model_loaded: true`, `database_connected: false`.
- A model-backed multipart API test loaded the existing checkpoint, generated a five-class result and `conv_head` Grad-CAM, and checked probability normalization. Unit and API tests cover image signature/size/decode validation, QC, patient/screening failure behavior without a database, role gating, and mocked Supabase RPC/storage call shapes.
- Latest full executed command: `& 'C:\Users\HP\.conda\envs\py311\python.exe' -m pytest backend/tests ai_model/tests -q -p no:cacheprovider --basetemp=C:\Users\HP\NETRAVA_1\.pytest-tmp` -> **75 passed in 19.03s** (2026-11-03).
- `pip check` -> no broken requirements. Supabase client import -> passed after installing `supabase 2.33.0`, already declared in `backend/requirements.txt`.
- Checkpoint size: 43,377,043 bytes. SHA-256: `3578BC6B7CA2112DB9D1B5908368953BE833A2B86027DECC734EEF92C0FA250D`. It was not changed.
- Supabase SDK check in the selected Python 3.11 environment: installed (`supabase 2.33.0`).
- Earlier complete local backend + AI run on 2026-11-03: **72 passed in 16.51s**. This contained no live Supabase checks.

## Backend fixes made

- Corrected the predictor argument and result-field mapping between FastAPI and `NetravaPredictor`.
- Restricted locally signed JWT acceptance to test mode. Non-test requests validate with Supabase Auth and use the database-backed role and clinic profile.
- Bound patient, screening, prediction, report, and media paths to the trusted clinic ID. Missing persistence now returns an error or an explicit `not_configured` status instead of fabricated IDs/URLs.
- Added transactional Supabase RPC paths for patient, screening, prediction, and review writes. Reviews and other clinical writes append audit events. Added best-effort media cleanup on failed writes.
- Added an initial local SQL migration, private storage/RLS declarations, health connectivity probing, production secret checks, and root-relative checkpoint path resolution.
- Added API regression and mocked persistence/storage tests; refreshed the generated OpenAPI contract and backend documentation.

## Not verified / blockers

- At initial verification, no root or backend `.env` existed. A root `.env` was later created and configured; secret values are not included in this report. Keep the service-role/secret key backend-only. `.gitignore` ignores `.env` and `.env.*`, while allowing `.env.example`. The Supabase SDK is installed. There is no `DATABASE_URL`, PostgreSQL driver, `psql`, or Docker runtime for direct catalog inspection.
- The migration has **not** been applied. PostgreSQL syntax/runtime, live JWT validation, table/RLS behavior, transaction RPCs, bucket access, signed URL generation, and persistence are **not verified**.
- Live table names and columns were partially inspected through the read-only PostgREST OpenAPI schema. Direct inspection of SQL constraints, all foreign keys, indexes, and `pg_policies` was not possible without a read-only PostgreSQL connection or schema-only export. The live schema differs substantially from the local migration and backend queries; details are recorded below. The migration contains policy creation statements and an `ON CONFLICT` bucket update, so do not apply it to the existing project without a full schema/policy comparison and explicit approval.
- After configuration, read-only OpenAPI, zero-row table/relationship, Auth health, and bucket metadata requests were performed. Results and limits are recorded below. No record rows were requested, and no files or database state were changed.
- During the initial server check, `/api/v1/health` reported `degraded` because the database was not configured then. The server health endpoint has not been rerun under the current environment; application workflows have not been tested against the live schema.
- The report API returns structured JSON; PDF export and audit-log viewing are not implemented. Login-attempt audit records and GPU/CPU metrics are also absent.
- There is no `.git` directory; `git status` and a Git diff cannot show pre-existing changes. No frontend files or model files were modified.
- Test warning: `pytest-asyncio` reports that `asyncio_default_fixture_loop_scope` is not set. The existing screening route test also emits a Starlette deprecation warning for a status-code constant.

## Current gate

Backend phases are not complete. The existing project is reachable, but the live schema and REST contract conflict with the current migration and several backend query shapes. Keep Flutter work paused until the backend is reconciled to the existing schema, security is verified, and the owner approves the frontend phase.

## Phase 3 connection-check result (2026-11-03)

- Supabase REST connectivity: **verified** (REST OpenAPI, all ten zero-row table queries, and service-key `clinics` query returned HTTP 200).
- Table names and columns: **partially inspected** using PostgREST OpenAPI; selected relationship embeds for profile→clinic, screening→patient, image→screening, prediction→image/probabilities/explanations, and report→screening/prediction returned HTTP 200. SQL constraints, complete FK definitions, indexes, and policies remain **not inspected**.
- Supabase Auth health endpoint: **HTTP 200**. User login and Supabase-issued JWT/profile validation: **not verified**.
- The three expected buckets exist and are **private** in bucket metadata. Bucket metadata returned no explicit file-size or allowed-MIME limits. Upload/download/signed-URL operations and object policies are **not tested**.
- Patient, screening, prediction, report, and audit persistence: **not tested live**. Local tests verify mocked RPC/storage call contracts only.
- Anonymous-key `patients?select=id&limit=0` returned HTTP 200 with zero rows requested. This does **not** prove patient rows are publicly readable or protected; RLS can silently filter rows. Treat anonymous-read behavior as unresolved until policies are inspected and tested with controlled identities.
- Patient, screening, prediction, report, and audit persistence: **not tested live**. Local tests verify mocked RPC/storage call contracts only. The backend's expected write RPC names are not listed in the current service-key REST OpenAPI (`register_clinic_patient`, `create_screening_records`, `write_screening_prediction`, `write_screening_review`); live OpenAPI instead exposes `current_user_clinic`, `current_user_role`, and `rls_auto_enable`. The latter was not called; inspect its definition and grants before use.
- Before declaring Phase 3 complete: obtain a schema-only export including policies, constraints, indexes, and function definitions; reconcile local code with the existing normalized schema; review `rls_auto_enable`; then run auth/RLS checks using controlled test accounts and an isolated development environment for writes/storage. Do not apply the current migration.

## Safe configuration verification (2026-11-03)

- Root `.env` exists. The backend `Settings` loader read non-empty values for `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SECRET_KEY`, and `ENVIRONMENT`; the URL was HTTPS and the environment value was valid. Secret values were never printed.
- `.gitignore` contains `.env` and `.env.*` ignore rules and the `!.env.example` exception.
- Selected Python 3.11 environment initialized Supabase clients with both the publishable key and server-side secret key. Client construction alone does not prove remote access.
- One remote read-only request using the server-side key returned HTTP 200 for `GET /rest/v1/clinics?select=id&limit=0`; body suppressed, zero rows requested. This confirms project REST connectivity and query access for this key, not end-user authentication or RLS.
- No SQL, migration, table/policy/bucket change, record write, storage operation, AI change, or frontend change was performed. User JWTs, RLS, clinic isolation, and live data persistence still require separate verification.

## Combined backend mission — live schema and workflow compatibility (2026-11-03)

### Live REST schema observed (metadata only)

The service-key OpenAPI spec lists these existing table columns:

| Table | Live columns returned by OpenAPI |
|---|---|
| `clinics` | `id`, `clinic_name`, `address`, `phone`, `email`, `is_active`, `created_at` |
| `user_profiles` | `id`, `full_name`, `role`, `clinic_id`, `phone`, `is_active`, `created_at`, `updated_at` |
| `patients` | `id`, `patient_code`, `full_name`, `date_of_birth`, `sex`, `phone`, `email`, `medical_notes`, `clinic_id`, `created_by`, `created_at`, `updated_at` |
| `screenings` | `id`, `patient_id`, `technician_id`, `clinic_id`, `screening_date`, `status`, `notes`, `created_at`, `updated_at` |
| `retinal_images` | `id`, `screening_id`, `eye_side`, `storage_bucket`, `storage_path`, `original_filename`, `mime_type`, `file_size_bytes`, `image_width`, `image_height`, `uploaded_by`, `uploaded_at` |
| `predictions` | `id`, `retinal_image_id`, `model_name`, `model_version`, `predicted_grade`, `confidence`, `referral_recommended`, `inference_time_ms`, `created_at` |
| `prediction_probabilities` | `id`, `prediction_id`, `dr_grade`, `probability` |
| `explanations` | `id`, `prediction_id`, `explanation_type`, `storage_bucket`, `storage_path`, `target_layer`, `created_at` |
| `reports` | `id`, `screening_id`, `prediction_id`, `reviewer_id`, `ai_summary`, `clinical_assessment`, `final_grade`, `review_status`, `storage_bucket`, `storage_path`, `reviewed_at`, `created_at` |
| `audit_logs` | `id`, `user_id`, `action`, `table_name`, `record_id`, `details`, `created_at` |

Every expected table's zero-row `select=id&limit=0` query returned HTTP 200 with the service key. Selected PostgREST relationship embeds also returned 200: profile→clinic, screening→patient, retinal image→screening, prediction→image/probabilities/explanations, and report→screening/prediction. These probes fetched no records. OpenAPI does not expose SQL indexes, RLS policies, or complete constraint definitions.

### Compatibility failures observed

Zero-row requests matching existing backend query shapes returned HTTP 400 / PostgreSQL `42703` (undefined column):

- Auth profile lookup requests `user_profiles.active` and `clinics.name`; live fields are `is_active` and `clinic_name`.
- Patient search requests `patients.mrn`; live field is `patient_code` (and patient sex/contact/creator fields also use different names).
- Prediction image authorization filters `retinal_images.clinic_id`; that column is absent from the live table.
- Report retrieval filters `reports.clinic_id`; that column is absent from the live table.

The live database normalizes five class probabilities into `prediction_probabilities` and Grad-CAM paths into `explanations`. The local migration instead adds a JSONB `predictions.probabilities` field and `predictions.gradcam_heatmap_path`. Live `predictions`, `reports`, and `audit_logs` also differ in confidence/referral, review, and actor/resource columns. Several backend-required write RPCs are not listed in the live OpenAPI. These are confirmed incompatibilities, not guesses based on the local migration.

The live REST OpenAPI also lists `POST /rpc/rls_auto_enable`. It was not invoked. Its function body and execute grants are not visible in the API spec; review them via a schema-only export before trusting or calling it.

### Workflow status

- **Authentication:** Auth service health returned HTTP 200. User login/JWT was not tested; the backend profile query is incompatible with live column names and would fail.
- **Patient:** list/create routes exist locally, but create depends on a write RPC not listed in live OpenAPI; search uses the absent `mrn` field. Single-patient retrieval/update routes are missing. No patient rows were read or written.
- **Screening/image:** validation and QC have local tests. Live bucket `fundus-images` exists and is private. No upload was attempted. The local screening RPC is not listed in live OpenAPI; live image column names differ, so persistence is blocked.
- **Prediction/Grad-CAM:** full-checkpoint five-class inference and Grad-CAM are covered by local tests; grade ≥2 referral behavior is asserted. Live authorization query fails on missing `retinal_images.clinic_id`; persistence depends on an unexposed RPC and incompatible column design. No model/storage/database changes were made.
- **Reports/audit:** APIs and mocked RPC tests exist locally. Live report lookup fails on missing `reports.clinic_id`; write RPC is not listed in live OpenAPI; audit column names differ. PDF report generation is not implemented. No report/audit write was attempted.
- **Storage/security:** all expected buckets are present/private. Metadata returned null/empty for explicit file-size and allowed-MIME limits. Upload, object retrieval, signed URLs, storage policies, live user JWT, RLS, cross-clinic isolation, and non-empty anonymous access remain unverified. Anonymous zero-row patient query returned 200 but returned no rows; this is not an RLS pass.
- **Secrets/logging:** root `.env` is ignored by the existing rules and was never printed. No service-role-key references were found in Flutter source. Hardened local logs to omit user-supplied validation values, filenames, patient/resource IDs, and raw backend exception text; added regression tests.

### Proposed reconciliation (not applied)

Preserve the existing normalized live tables. First obtain a schema-only export including `pg_policies`, FK/unique/check constraints, indexes, storage policies, and function bodies/grants. Then update backend query/response mappers to the live column names and normalized probability/explanation tables. Do not silently discard the structured diabetes intake fields missing from live `patients`; decide whether to add those fields through a reviewed additive migration. Prepare narrowly scoped transactional write functions for patient, screening/image, prediction/probabilities/explanation, report, and audit only after reviewing existing triggers/policies/functions. Review and restrict `rls_auto_enable` if needed. A tailored additive migration and policy/bucket changes require owner approval; the current migration must not be run against this project.

**Backend readiness:** not ready for Flutter integration. Local AI/API tests pass, but critical live workflow queries and write functions are incompatible/unverified, and RLS/user authentication have not been demonstrated.

## Latest continuation verification (2026-11-03)

### Safe local changes

- Added authenticated `GET /api/v1/patients/{patient_id}` with both patient ID and trusted clinic ID in the database query.
- Mapped patient list/detail reads to the live column names previously observed (`patient_code`, `sex`, `phone`, `medical_notes`, and related fields). Patient registration still depends on structured intake columns and a transactional function that have not been reconciled with the live schema.
- Fixed prediction image authorization to filter through the existing `retinal_images → screenings` relationship and `screenings.clinic_id`. A regression test checks the query relationship and the not-found behavior.
- Added validated local clinical PDF generation and a private-bucket upload helper. PDF generation and upload adapter behavior are tested with synthetic data/mocked storage. There is no live report metadata write or download endpoint because the live report schema/function contract remains unresolved.
- Regenerated `shared/api_contracts/openapi_contract.json` from FastAPI and added the patient detail endpoint to the API reference. No Flutter files, model weights, database data, migration, policies, or storage objects were changed.

### Latest tests and runtime checks

- Final selected Python 3.11 command `python -m pytest -c backend\pytest.ini backend/tests ai_model/tests -q -p no:cacheprovider --basetemp=C:\Users\HP\NETRAVA_1\.pytest-temp-configured`: **87 passed in 16.10s**. This covers local unit/API behavior, real checkpoint inference and Grad-CAM, synthetic PDF rendering, patient and prediction clinic-query regressions, and mocked storage/database interactions; it is not a live persistence test. No fixture-scope warning was emitted.
- Uvicorn started from the project root and loaded the existing checkpoint. `/api/v1/health`, `/api/v1/docs`, and `/api/v1/openapi.json` returned HTTP 200; health was `degraded` (`model_loaded=true`, `database_connected=false`). Missing-token patient access returned HTTP 401. The local process was stopped after verification.
- The root `.env` exists and all five required settings were present in the loader; no values were printed. Current session's read-only Supabase `clinics` request failed with `ConnectError`; no live request body or secret was printed. Earlier successful read-only schema/table/bucket metadata checks remain evidence for those earlier checks only. Current live connectivity is not verified by this session.
- `pip check`: no broken requirements. Checkpoint remains 43,377,043 bytes with SHA-256 `3578BC6B7CA2112DB9D1B5908368953BE833A2B86027DECC734EEF92C0FA250D`.
- Set `asyncio_default_fixture_loop_scope = function` in `backend/pytest.ini`; the final configured run reported no pytest-asyncio scope warning. The initial root invocation did not load this backend-local config, so the final command explicitly uses `-c backend\pytest.ini`.
- The saved OpenAPI contract was compared to the current runtime FastAPI schema: exact match, 8 paths, including the new patient detail route.

### Remaining acceptance blockers

- Current session could not reach Supabase. Even if reachable, complete schema inspection still needs a schema-only export for types, foreign keys/constraints/indexes, policies, storage policies, and function bodies/grants.
- Supabase-issued user JWT login/profile lookup, inactive-user behavior against real accounts, RLS, clinic isolation, object upload/retrieval/signed URLs, and any live persistence are not verified. The repo's local migration conflicts with the existing normalized live schema and remains unapplied.
- Patient update, full screening/image retrieval, normalized prediction/explanation persistence/retrieval, report metadata save/download, and audit-log workflows are not complete end-to-end. Do not claim the backend phases are complete or start Flutter work until schema reconciliation and safe controlled integration verification are complete.
