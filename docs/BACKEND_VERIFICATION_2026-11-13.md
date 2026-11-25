# Backend verification ? 2026-11-13

## Status: NOT READY ? remaining blockers

The current code was inspected without rebuilding the project. This directory has no Git metadata, so recent changes cannot be attributed or compared to a commit baseline. Existing frontend and checkpoint files were preserved.

## Verified results

- Project `.venv`: Python 3.11.9. Conda is unnecessary. `pip check`: no broken requirements.
- Full suite: **94 passed, 6 warnings in 15.66s**, no failures or skips. Command: `.\.venv\Scripts\python.exe -m pytest -c backend/pytest.ini backend/tests ai_model/tests -q -p no:cacheprovider --basetemp=.pytest-review-complete`.
- Application lifespan startup and shutdown succeeded through TestClient in development configuration. The real EfficientNet-B3 checkpoint loaded on CPU. Health returned HTTP 200, healthy, model_loaded=true, database_connected=true. This is connectivity health, not proof of persistence readiness.
- Swagger and OpenAPI returned 200. Missing-token requests to /auth/me and /patients returned 401. Localhost:3000 authorization CORS preflight returned 200.
- Read-only live Supabase Auth health and PostgREST OpenAPI returned 200. No patient rows, passwords, keys, or tokens were printed. No live writes, migrations, policy changes, bucket changes, or account creation occurred.

| Endpoint | Status | Result |
|---|---|---|
| Health | Verified | Development lifespan: 200, model and database reachable |
| Login | Offline success/failure verified; live blocked | Mocked GoTrue token exchange, correct public key, bearer response, invalid credentials 401; no test credentials found |
| Auth Me | Offline success/failure verified; live blocked | Exact login token forwarded to /auth/v1/user with public key; service key restricted to profile lookup; trusted profile matches login; missing/invalid/expired tokens tested |
| Create Patient | Offline RPC/error coverage; live blocked | Required register_clinic_patient RPC absent from exposed schema |
| List Patients | Offline coverage; live unverified | Clinic filters and search validation tested |
| Patient Details | Offline coverage; live unverified | Clinic-scoped detail and not-found tests |
| Create Screening | Offline coverage; live blocked | Image validation/QC/storage mocks; create_screening_records RPC absent |
| AI Predict | Real local inference verified; live persistence blocked | Actual checkpoint and conv_head Grad-CAM; 5 probabilities; write_screening_prediction RPC absent |
| Submit Report | Offline coverage; live blocked | Role gate and transactional call tested; write_screening_review RPC absent |
| Get Report | Offline coverage; live unverified | Clinic-scoped retrieval; normalized live schema cannot round-trip all request fields |

## Findings and fixes

- `pyproject.toml`: removed an activation command accidentally appended to build-backend; TOML parsing prevented all tests.
- `backend/requirements.txt`: declared missing matplotlib dependency. Installed it into the existing .venv; Grad-CAM import now succeeds.
- `backend/app/core/security.py`: stopped logging raw upstream authentication response bodies, which may contain sensitive provider data. Authentication architecture and public contracts preserved.
- `backend/app/services/patient_service.py`, `screening_service.py`, `prediction_service.py`, `report_service.py`: removed nontransactional missing-RPC fallbacks. Those paths bypassed the intended atomic audit contract, swallowed audit errors, allowed partial multi-table saves, and the report fallback did not enforce clinic scope. Missing RPCs now fail closed through existing errors. Screening exception logging now records exception type only.
- `backend/app/services/report_pdf.py`: fixed unsupported HTTP_422_UNPROCESSABLE_CONTENT constant for installed Starlette; invalid UUIDs now return the intended 422.
- `backend/app/ml/image_validator.py`: bounded upload reads to limit+1; verify original encoded image before RGB conversion; enforce pixel limit before decode.
- `backend/tests/test_auth_flow.py`: new provider-transport integration test passes the returned login token into /me, asserts exact token and correct public/service key usage, and covers invalid credentials.
- `backend/tests/test_persistence_services.py`: four regressions ensure missing RPCs never fall back to direct table writes.
- `backend/tests/test_image_validator.py`: regression for bounded upload reads.
- `backend/README.md`: corrected startup/test interpreter to project .venv and root environment template.
- `shared/api_contracts/openapi_contract.json`: regenerated with installed supported FastAPI/Pydantic versions. Generator differences concern file-upload schema representation, validation schema, nested profile reference and bearer description. Route/request/response fields were not intentionally changed.
- Documentation: this report, PROJECT_HANDOFF, WORK_LOG, IMPLEMENTATION_PLAN and API_DOCUMENTATION updated with current evidence and blockers.

## Model status

Strict checkpoint loading, eval mode, CPU inference, five-class mapping/probability normalization, 300x300 LANCZOS aspect-preserving black padding, ImageNet normalization, and conv_head Grad-CAM are covered by passing tests. Existing real retinal fixtures and synthetic-image API inference ran. No weights, architecture, class ordering or training preprocessing changed. CUDA was not exercised; current configuration explicitly uses CPU. Tests establish software behavior, not clinical validation.

## Supabase status and remaining blockers

1. **Controlled login credentials unavailable.** Root .env contains only ENVIRONMENT, SECRET_KEY, SUPABASE_URL, SUPABASE_KEY and SUPABASE_SERVICE_ROLE_KEY. No email/password credential variables were found in the process environment; backend contains only .env.example. The user indicated an account exists, but no usable account location was supplied. Consequently the historical INVALID_TOKEN root cause cannot be established or claimed fixed. Public-key verification and trusted profile loading work in controlled mocked tests only.
2. **All four required write RPCs absent from service-role REST metadata.** Only rls_auto_enable, current_user_clinic and current_user_role are exposed. Database operations cannot safely complete the intended workflow. The earlier migration conflicts with the normalized live database; do not apply it blindly. Need a schema-only export with types, constraints, policies, indexes, function bodies and grants, then a reviewed compatible migration/RPC implementation.
3. **Live RLS, clinic isolation, storage object permissions and persistence not verified.** Need controlled accounts across clinics and an isolated development write target after schema reconciliation. Service-role connectivity does not prove end-user access isolation.
4. **Report semantics incomplete against normalized live schema.** Current normalized mapping cannot persist/retrieve every report field (urgent referral/override/original AI grade). PDF helper works locally but is not wired to report metadata/download API. Reconcile without fabricating values.

Warnings are dependency deprecations and Pydantic model_ namespace warnings; they did not fail tests. Frontend integration remains gated until the actual authenticated end-to-end workflow passes.
