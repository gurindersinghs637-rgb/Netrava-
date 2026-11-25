# NETRAVA final backend readiness report

Verified on 2026-11-13, Asia/Kolkata. This report supersedes earlier readiness notes.

## 1. Overall status

**NOT READY FOR FRONTEND**

The remaining implementation has been completed locally, including compatible SQL
migration/RPCs, complete report persistence, PDF retrieval, clinic RLS and API tests
against actual PostgreSQL. The remaining acceptance gate is deployment and live
account/Storage verification. No hosted schema, policies, accounts, records or
objects were changed in this continuation. Flutter and model weights are unchanged.

## 2. Endpoint verification

All routes below use the `/api/v1` prefix. “Actual SQL” means execution in isolated
PGlite PostgreSQL, not the hosted database. Auth identities and object storage in
the local API workflow use controlled adapters. Unit/provider-transport tests are
identified separately from live evidence.

| Endpoint | Authentication | Database | ML | Tests | Status |
|---|---|---|---|---|---|
| GET /health | Public | Live read-only connectivity verified earlier today | Real startup load verified | Health/startup tests | 200; connectivity is not migration readiness |
| POST /auth/login | Public, GoTrue credentials | Trusted active profile + active clinic required | N/A | Mocked token exchange, success/rejection | Implemented; live account verification pending |
| GET /auth/me | Supabase bearer | Service-only trusted profile lookup | N/A | Exact returned-token forwarding, invalid/expired/missing tokens, disabled clinic/profile | Implemented; live account verification pending |
| POST /patients | Technician, ophthalmologist, administrator | Actual register_clinic_patient RPC, audit + unique MRN | N/A | Actual SQL/API 201 and duplicate 409 | Local workflow passed; hosted migration pending |
| GET /patients | Any trusted active clinic role | Actual clinic-scoped SELECT, pagination | N/A | API and query-filter tests | Local workflow passed |
| GET /patients/{patient_id} | Any trusted active clinic role | Actual clinic-scoped SELECT, diabetes-field roundtrip | N/A | Actual SQL/API, other clinic 404 | Local workflow passed |
| POST /screenings | Technician, ophthalmologist, administrator | Actual screening/image/audit RPC; object storage adapter | Upload validation + QC | Actual SQL/API 201; other clinic 404 | Local workflow passed; live Storage pending |
| POST /predict | Technician, ophthalmologist, administrator | Actual prediction + five normalized probabilities + explanation + audit | Real checkpoint and conv_head Grad-CAM | Actual SQL/API 200; other clinic 404 | Local workflow passed; live Storage pending |
| POST /screenings/{screening_id}/report | Ophthalmologist, administrator | Actual review RPC; complete fields; immutable signed review | Uses persisted prediction association | Actual SQL/API 200, technician 403, signed edit 409 | Local workflow passed |
| GET /screenings/{screening_id}/report | Any trusted active clinic role | Actual clinic-scoped report read | N/A | Full saved/loaded response equality; other clinic 404 | Local workflow passed |
| GET /screenings/{screening_id}/report/pdf | Any trusted active clinic role | Persisted patient/screening/prediction/probabilities/report | Persisted AI result in PDF | Actual API/PDF signature; other clinic 404; rendered visual QA | Local workflow passed |

Patient updates were not an existing implemented API contract and were not added.
This continuation adds the PDF download route and optional diabetes detail response
fields. Existing URLs and required request/response fields are preserved. The
shared OpenAPI JSON has been regenerated.

## 3. Authentication status

Login -> returned token -> `/auth/me` passes controlled HTTP-provider transport
tests using the non-test authentication code. Tests assert that the exact token
returned by GoTrue is sent to `/auth/v1/user`, with the public/anon key. Profile
queries use only the backend service key. Role and clinic membership are loaded
from trusted database rows; inactive users or clinics are rejected. Provider outages
return 503 rather than incorrectly treating every upstream error as an invalid JWT.

The root `.env` has no account email/password, and no usable account credential
location was provided. No real user session was fabricated or issued with the
service-role key. The historical `401 INVALID_TOKEN` incident cannot be assigned a
proven root cause without that live request. The account verification script below
forwards the returned token automatically, eliminating manual copy/paste ambiguity.
Swagger still accepts the raw access token in Authorize and adds `Bearer` itself.

Raw upstream auth bodies, raw SQL errors, transport URLs/headers and local-variable
tracebacks are excluded from application logs. No credentials or tokens were
printed, stored in source, or added to documentation.

## 4. Database and Supabase status

### Schema and migration

The live REST schema metadata for these ten tables was read successfully:
`clinics`, `user_profiles`, `patients`, `screenings`, `retinal_images`, `predictions`,
`prediction_probabilities`, `explanations`, `reports`, `audit_logs`. No patient rows
were retrieved. A metadata-only snapshot is checked in under `supabase/`.

Added `supabase/migrations/202611130001_normalized_backend.sql`. It supports an
empty Supabase project and the observed normalized existing schema. The original
conflicting migration is preserved in `supabase/legacy/`; it must not be applied.

The new migration implements:

- `register_clinic_patient(jsonb)`: structured intake, clinic/staff validation,
  per-clinic duplicate protection and atomic audit insertion.
- `create_screening_records(jsonb,jsonb)`: patient/clinic association, real upload
  dimensions/byte count/MIME, QC, content SHA-256 and audit in one transaction.
- `write_screening_prediction(jsonb)`: clinic/staff verification, five normalized
  probabilities, probability/confidence/referral validation, explanation and audit.
- `write_screening_review(...)`: clinician/administrator gate, prediction
  association, original grade + override + notes + urgency, serialized review writes,
  signed-review immutability/idempotency and atomic audit.
- Narrow staff/report/RLS helpers; client execution of all write functions is
  revoked. Write RPCs run with service-role privileges rather than security-definer
  escalation. The RLS clinic lookup is a narrowly scoped security-definer helper.

Required missing intake/report/image fields are added without discarding existing
data. Historical reports with unknown original grade/urgency return a clear 409
requiring clinician review; unknown values are not fabricated as grade zero/false.

### RLS, roles and isolation

The migration enables RLS on all ten tables, adds restrictive clinic policies that
cap existing permissive policies, restricts direct clients to reads, and limits
profile reads to the current user. Indirect image/prediction/probability/explanation
and report ownership follows the screening's clinic. Audit records are append-only.
Existing medical buckets must be private; permissive Storage policies cannot grant
anonymous/authenticated direct access to those buckets. Other buckets are unaffected.

Actual PostgreSQL checks proved clinic isolation, inactive profile/clinic rejection,
technician review rejection, administrator permission, service-only RPC execution,
and resistance to an intentionally broad legacy SELECT policy. Hosted RLS has not
yet been verified because this migration has not been deployed there.

Duplicate legacy rows or conflicting hosted constraints/triggers may cause the
transaction to fail and roll back. Do not delete records or bypass constraints to
force deployment. The REST snapshot cannot establish hosted trigger/function bodies.

## 5. ML status

- Checkpoint: `ai_model/checkpoint/best_efficientnet_b3_staged.pth`.
- SHA-256 unchanged: `3578bc6b7ca2112db9d1b5908368953be833a2b86027decc734eef92c0fa250d`.
- Strict EfficientNet-B3 weight loading and eval mode verified on CPU.
- Training preprocessing preserved: 300x300 aspect-preserving LANCZOS resize,
  black padding and ImageNet normalization.
- Real inference, five-class grade mapping, normalized probabilities and conv_head
  gradient/heatmap generation passed. No retraining or architecture change.
- Non-test prediction requires the upload hash to match the screening image. Older
  images without a hash require a new screening upload (409); mismatches return 422.
- Explanation upload failure returns 503; it no longer silently reports success.
  Each analysis uses a unique heatmap path to avoid overwriting earlier artifacts.
- CUDA and clinical accuracy were not evaluated in this continuation. QC measures
  sharpness/illumination; it is not a trained detector of whether an image is retinal.

## 6. Tests and evidence

| Verification | Passed | Failed | Skipped |
|---|---:|---:|---:|
| Backend + model pytest suite | 114 | 0 | 0 |
| Isolated actual-PostgreSQL assertions | 50 | 0 | 0 |
| FastAPI + actual SQL + real model workflow checks | 16 | 0 | 0 |

The SQL assertions are checks rather than additional pytest test cases. The API
workflow also invokes the 50-check SQL baseline; do not count that baseline twice.
Combined backend statement coverage from pytest plus the actual-SQL workflow is
**85%**. Pytest reports six existing dependency deprecation/Pydantic namespace
warnings. `pip check` reports no broken installed requirements. Python compilation
checks pass. Final PDF layout was rendered and visually checked with long names,
full UUIDs, multi-page output, clinical fields and synthetic image content.

Reproduce from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -c backend/pytest.ini backend/tests ai_model/tests -q -p no:cacheprovider --basetemp=.pytest-readiness-check --cov=backend.app
npm.cmd ci --prefix scripts/database_test --no-audit --no-fund
node scripts/database_test/verify.mjs
.\.venv\Scripts\python.exe -m coverage run --append --source=backend.app scripts/database_test/verify_api_workflow.py
.\.venv\Scripts\python.exe -m coverage report
```

The local API workflow runs in development mode with trusted test identities and
in-memory object-storage adapters. All clinical persistence calls execute the
actual migration functions in PostgreSQL; model inference is real. It does not
claim live Auth/Storage verification.

## 7. Exact manual actions required

Only deployment and real-account verification remain. This environment has a
service-role REST key but no direct SQL connection, Supabase management connector,
or account password. REST credentials do not provide a SQL execution endpoint.

1. In the intended **development** Supabase project's SQL Editor, run the complete
   `supabase/migrations/202611130001_normalized_backend.sql`. Do not run anything in
   `supabase/legacy/`. The migration commits as one transaction; investigate any
   failure before proceeding. Existing rows and bucket visibility are preserved.
2. Use existing active test accounts: an ophthalmologist/administrator in clinic A
   and a user in clinic B. Their `user_profiles.id` must match Auth user IDs; profile
   and clinic `is_active` must be true. If missing, provision them privately through
   Supabase Dashboard. Never share passwords or tokens in chat.
3. From the repository root run this **single verification procedure**:

   ```powershell
   .\.venv\Scripts\python.exe scripts/verification/verify_live_backend.py
   ```

   It prompts locally, hides passwords, automatically forwards the login token into
   `/auth/me`, and creates clearly marked synthetic DEMO patient/screening/report
   records. It checks patient roundtrip, real inference, probabilities, Grad-CAM
   signed-media downloads, public-media rejection, complete report roundtrip, PDF,
   other-clinic API rejection and direct REST RLS isolation. Demo records and
   immutable audit events are retained; it asks for explicit YES before writing.
   Use an actual retinal image; the bundled retinal fixture is the default.
   Only pass/fail labels and HTTP statuses are printed. No token/password/provider
   bodies are printed. Exit 0 means all checks passed; exit 2 means cross-clinic
   checks were omitted; exit 1 means verification failed. Do not treat 1 or 2 as
   readiness approval. Do not weaken auth or use service-role tokens as user tokens.

After migration deployment and exit-0 live verification, record that result here
before declaring READY FOR FRONTEND. Until then, the deployed backend's end-to-end
acceptance remains unverified even though implementation and local tests pass.


## Important implementation files

- `backend/app/services/{patient,screening,prediction,report}_service.py`: normalized
  persistence mappings, full metadata, image binding and safe failure behavior.
- `backend/app/services/database_errors.py`: stable SQLSTATE-to-API error mapping.
- `backend/app/services/report_pdf.py`, `backend/app/api/v1/screening.py`: persisted
  PDF download and wrapped, visually verified clinical report layout.
- `backend/app/services/auth_service.py`, `backend/app/core/{security,logging}.py`:
  active-clinic validation, provider outage classification and secret-safe logs.
- `backend/app/schemas/patients.py`: demographic validation and structured intake readback.
- `backend/tests/`: expanded auth, report, image-integrity and database-error tests;
  conftest clears live credentials so unit tests cannot accidentally hit hosted APIs.
- `supabase/migrations/202611130001_normalized_backend.sql`: compatible normalized DDL,
  four transactional RPCs, RLS, audit integrity and media restrictions. Original
  migration preserved unchanged in `supabase/legacy/`.
- `scripts/database_test/`: pinned Node test dependency/lockfile, actual PostgreSQL
  execution harness and FastAPI/SQL/model workflow. Also verifies additive migration
  against the original normalized table shape with a pre-existing synthetic row.
- `scripts/verification/verify_live_backend.py`: private live acceptance procedure.
- `backend/requirements.txt`, `pyproject.toml`, `.gitignore`: declared email validation
  dependency, included ML package in distribution discovery, excluded local test/runtime data.
- Shared OpenAPI, backend/Supabase runbooks, roadmap, handoff and work log updated.


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
