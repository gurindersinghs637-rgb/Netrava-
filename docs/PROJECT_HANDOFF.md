# NETRAVA Backend Handoff

**Updated:** 2026-11-03  
**Workspace:** `C:\Users\HP\NETRAVA_1`  
**Python:** `C:\Users\HP\.conda\envs\py311\python.exe` (Python 3.11)

## Current status

Continue backend-only. Do not start Flutter development until all three backend phases are verified and the owner approves. The Flutter welcome/login prototype and the trained checkpoint are preserved.

FastAPI starts from the repository root with:

```powershell
& 'C:\Users\HP\.conda\envs\py311\python.exe' -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

At the prior live-server check (port 8003, before root `.env` was configured), startup loaded the model, docs/OpenAPI returned 200, protected routes rejected missing tokens with 401, and login without Supabase config returned 503. Health then reported `degraded` (`model_loaded=true`, `database_connected=false`). Port 8000 was already occupied by a separate process during that earlier task, so it was left untouched. The backend server was not restarted during the current read-only schema audit.

## Work completed in this continuation

- Fixed the API-to-model call signature and mapped prediction grade, confidence, probabilities, and Grad-CAM output to the actual inference schema.
- Limited locally signed tokens to `ENVIRONMENT=testing`; non-test auth validates Supabase access tokens and loads trusted active role/clinic data from `user_profiles`.
- Added clinic filters and role gates for patient, screening, prediction, and report APIs.
- Removed fabricated local storage URLs and fabricated prediction IDs. Missing database configuration now fails closed for writes; test-mode prediction responses identify non-persistence.
- Added transaction RPC calls and clinic-scoped private-media object paths. Added local migration for schema, RLS, buckets, audit events, and report/review persistence.
- Added real-checkpoint API inference/Grad-CAM tests, QC tests, and mocked database/storage contract tests.
- Updated API/OpenAPI, backend, security, Supabase, audit, roadmap, and work-log documentation.

## Test results

```powershell
& 'C:\Users\HP\.conda\envs\py311\python.exe' -m pytest backend/tests ai_model/tests -q -p no:cacheprovider --basetemp=C:\Users\HP\NETRAVA_1\.pytest-tmp
```

Final result for the combined mission on 2026-11-03: **75 passed in 19.03 seconds**. Pytest emitted the existing `asyncio_default_fixture_loop_scope` deprecation warning. The suite includes real-checkpoint API inference/Grad-CAM, RPC/storage mocks, QC, and new regression tests confirming validation input, upload filenames, and backend exception details are not logged or echoed. Mock tests do not count as live Supabase verification.

`pip check` reported no broken requirements; `supabase 2.33.0` is installed into the selected Conda environment. No checkpoint or database data was modified.

## Supabase and remaining blockers

The root `.env` exists and is configured; the backend successfully loaded its required values. The SDK (`supabase 2.33.0`) is installed. Read-only PostgREST OpenAPI, zero-row table/relationship queries, Auth health, and Storage bucket metadata requests succeeded. The migration is local only and has not been applied. User JWT auth, RLS policies, Storage object operations, signed URLs, and persistence remain unverified. Several live columns and write-function endpoints conflict with the current backend.

The live table names and columns have now been partially inspected through the REST OpenAPI schema. The schema differs from both the backend query fields and the checked-in migration. The migration has a `predictions` JSONB `probabilities` field and a `gradcam_heatmap_path` field; the live database instead exposes separate `prediction_probabilities` and `explanations` tables. Do not blindly apply it: it contains non-idempotent `CREATE POLICY` statements and updates existing bucket privacy on conflict. See `PROJECT_AUDIT.md` for the observed column mismatches and next steps.

The project directory has no `.git` folder, so Git status/diff cannot establish the pre-existing change baseline. No Flutter files were modified. `PROJECT_AUDIT.md` contains the current architecture, verified functionality, limitations, and security boundary.

## Exact next task

The next task is to obtain a schema-only export including constraints, indexes, policies, storage policies, and function definitions/grants. Reconcile the FastAPI queries and local migration with the existing normalized live tables; review the exposed `rls_auto_enable` function before any use. The current migration must not be applied. After owner review, run authentication/RLS tests with controlled clinic test accounts, then writes/storage only in an isolated development setup. Keep Flutter paused until backend phases are verified and the owner approves it.

## Latest backend continuation (2026-11-03)

- **Full local suite:** Ran from the project root with the selected Python 3.11 interpreter: `python -m pytest backend/tests ai_model/tests -q -p no:cacheprovider --basetemp=C:\Users\HP\NETRAVA_1\.pytest-temp-final` → **87 passed in 17.12s**. This includes a real checkpoint prediction/Grad-CAM test, synthetic PDF generation and mocked report-storage tests, two patient-detail query/isolation tests, and two tests that assert prediction image authorization scopes through `retinal_images → screenings.clinic_id`. No live write tests were performed. A pytest-asyncio fixture-scope deprecation warning remains.
- Final rerun after making the pytest fixture loop scope explicit in `backend/pytest.ini`: `python -m pytest -c backend\pytest.ini backend/tests ai_model/tests -q -p no:cacheprovider --basetemp=C:\Users\HP\NETRAVA_1\.pytest-temp-configured` → **87 passed in 16.10s**, without the fixture-scope deprecation warning. This latest run supersedes the earlier 17.12-second result.
- An initial full-suite attempt without an explicit workspace temp directory had **83 passed and 2 setup errors** because Windows denied pytest access to the default AppData temp folder. Re-running with a new workspace temp directory resolved the environment issue; the suite then passed. An earlier backend-only run had two failures: one malformed assertion against `is_active`, and one test relied on a retinal image fixture file absent from the project. Corrected the assertion and made the real-checkpoint API test use the existing synthetic PNG generator. Neither fix changes model behavior or removes coverage.
- **Local server:** Uvicorn started using `backend.app.main:app`; model checkpoint loaded; startup completed. `/api/v1/health` returned HTTP 200 with `model_loaded=true`, `database_connected=false`, `status=degraded`. `/api/v1/docs` and `/api/v1/openapi.json` returned HTTP 200; OpenAPI listed 8 paths. Unauthenticated `GET /api/v1/patients` returned 401. Server was stopped cleanly after checks.
- **Current-session Supabase check:** Required settings were present without printing their values, but the read-only `clinics` request failed with `ConnectError` from this session's network. This run therefore does not verify current live connectivity. Earlier successful read-only schema/table/bucket checks remain documented above; they do not establish JWT/RLS or writes.
- Added clinic-scoped `GET /api/v1/patients/{patient_id}`, mapped patient list/detail queries to the previously observed live patient columns, and changed prediction authorization to use the confirmed `retinal_images.screening_id → screenings.clinic_id` relation. Added a focused regression test and regenerated `shared/api_contracts/openapi_contract.json` from the current FastAPI app.
- Added local PDF generation for validated synthetic/explicit report data and a private-bucket upload helper with mocked storage tests. It is not wired to live report metadata because report columns and write-function definitions are unresolved. Report retrieval/write and audit persistence remain blocked from safe completion.
- `pip check` reports no broken requirements. Checkpoint size and SHA-256 still match the recorded baseline: 43,377,043 bytes; `3578BC6B7CA2112DB9D1B5908368953BE833A2B86027DECC734EEF92C0FA250D`.
- **Exact next task:** Obtain a schema-only export from the existing Supabase project with column types, all constraints/indexes, RLS and storage policies, and function definitions/grants. Review the export without applying changes, then reconcile report and transactional write contracts and create a controlled development verification plan. No live writes or policy changes until the owner explicitly authorizes them. Flutter remains paused.

## Local Supabase configuration file setup (2026-11-03)

- Created the previously absent project-root `.env` without overwriting any file. It contains the owner's supplied project URL, placeholders for `SUPABASE_KEY` and `SUPABASE_SERVICE_ROLE_KEY`, a newly generated random `SECRET_KEY`, and `ENVIRONMENT=development`. The generated secret was not printed or copied into documentation.
- Updated root `.env.example` and `backend/.env.example` to contain placeholders only for secret-bearing entries. No actual API keys were requested or added.
- Confirmed `.gitignore` includes `.env` and `.env.*` ignore rules plus `!.env.example` allow rule.
- `backend/app/core/config.py` reads `.env` relative to the process working directory and its settings names match the template. The owner subsequently filled the key placeholders; the backend loaded each required value. Start from the repository root as documented. Do not paste the service-role secret into Flutter, chat, or documentation.
- At the time this file setup was recorded, no Supabase request had been made. The subsequent read-only connection check is documented below.

## Read-only Supabase configuration check (2026-11-03)

- The root `.env` exists and the backend settings loader successfully read non-empty `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SECRET_KEY`, and `ENVIRONMENT`. Values were not displayed. `.gitignore` ignores `.env`/`.env.*` and allows `.env.example`.
- Supabase SDK client construction succeeded locally for both configured keys. A single read-only request using the server-side key to `GET /rest/v1/clinics?select=id&limit=0` returned HTTP 200; the response body was suppressed and no rows were requested.
- Result: project REST connectivity and service-key query access for this endpoint are verified. This does **not** verify end-user login/JWT, RLS, clinic-level isolation, other table permissions, Storage, or persistence. No database state or files changed.
- Exact next task: inspect the existing live schema and policies safely, then plan targeted read-only checks for user authentication and clinic isolation. Do not run the local migration or perform writes before review/approval.


## Backend verification update ? 2026-11-13

Status: **BLOCKED / NOT READY FOR FRONTEND**. Project .venv (Python 3.11.9): **94 tests passed**, 6 warnings. Startup, model, health, Swagger, CORS and read-only Supabase connectivity verified. Live account credentials were not located. Four required transactional RPCs are absent from live REST metadata; unsafe direct-write fallbacks were removed. No live writes or migration changes performed. See [full verification report](BACKEND_VERIFICATION_2026-11-13.md) for files, endpoint results, root causes and blockers. No route or request/response field changes; shared OpenAPI regenerated with installed dependencies. Flutter remains paused.


## Backend implementation continuation - 2026-11-13

- Agent: Codex, backend/database/QA/documentation roles authorized by owner.
- Local implementation completed: normalized transactional RPC migration, structured
  intake, complete report field roundtrip, authenticated PDF retrieval, restrictive
  clinic RLS/backend-only storage policies, image hash binding and safe SQL errors.
- Legacy conflicting migration preserved in supabase/legacy; only the normalized
  migration remains in the active sequence. No hosted schema/data/policies changed.
- Verification: 114 pytest passed (0 failed/skipped); 50 actual PostgreSQL checks;
  16 FastAPI workflow checks with actual SQL and real model. Combined coverage 85%.
  PDF rendered/visually checked; checkpoint hash unchanged; pip check passes.
- Status: local implementation DONE; hosted deployment/live acceptance BLOCKED on
  owner SQL Editor action and privately run account/Storage verification. Flutter
  remains paused. The service-role REST key cannot execute arbitrary SQL.
- Handover: docs/FINAL_BACKEND_READINESS_REPORT.md is authoritative; it contains all
  endpoint results, the exact migration and one operator-run verification procedure.
  scripts/verification/verify_live_backend.py prompts privately and prints no secrets.


## Retinal verification fixture correction - 2026-11-13

The owner reports live authentication and patient APIs pass; screening stopped at
422 IMAGE_UNGRADABLE (original default blur score 6.26). Reproduced that score locally.
Production QC/threshold and upload validation are unchanged. The live verifier now
uses a documented fixed 400px LANCZOS derivative of bundled retinal source
001639a390f0.png (400x266, blur 69.47, optimal illumination). The source is untouched;
no sharpening/noise or dynamic QC-tuned transforms are used. This is a test-fixture
resolution choice, not a clinical-quality calibration.

Preflight runs the real validator/QC before login or database writes. Custom files
are checked unchanged. Both uploads reuse identical encoded bytes. Added helper
scripts/verification/retinal_fixture.py and regression tests; see
scripts/verification/README.md for the exact private command and offline preflight.
The local actual-SQL/model workflow passed all 16 API and 50 PostgreSQL checks with
the same retinal fixture, including screening, Grad-CAM, report/PDF and isolation.
The owner will rerun the full live procedure privately; credentials are not available
to this agent. No additional hosted changes or live verification were performed in
this fixture correction. READY FOR FRONTEND remains pending full live exit-0 proof.

Fixture correction validation: **119 passed, 0 failed, 0 skipped** (6 dependency warnings), 16.59 seconds. Production screening_service.py and image_validator.py were not modified.
