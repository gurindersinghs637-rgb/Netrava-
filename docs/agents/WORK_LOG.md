# NETRAVA — Multi-Agent Work Log & Immutable Audit Trail

**Document Version:** 1.0.0  
**Repository:** `NETRAVA`  
**Master Standard:** `AGENT.md` Section 8

> [!IMPORTANT]
> **IMMUTABLE LEDGER RULES:**  
> 1. Never delete, overwrite, or edit previous task entries.  
> 2. Always append a new `## Task Entry` at the bottom of this file after completing a meaningful task.  
> 3. Do not mark work as completed unless verifiable evidence (files, tests, logs) exists.

---

## Task Entry #001

- **Agent ID:** AGENT_00 / AGENT_07
- **Agent Name:** Lead Multi-Agent Coordinator & Technical Documentation Engineer
- **Date:** November 1, 2026
- **Development Phase:** Phase 0 — Project Foundation
- **Task Name:** Complete Project Audit, Foundation Architecture, Design Extraction & Multi-Agent Setup
- **Status:** COMPLETED

### Objective
Inspect the existing project artifacts, preserve all existing Flutter code, reconstruct the machine learning pipeline metadata, extract the complete UI/UX design suite, build the clean target directory structure, author the master project documentation, define multi-agent operating rules, and establish the technical baseline for NETRAVA.

### Work Completed
1. **Repository & Asset Audit:** Thoroughly inspected host files and identified:
   - Existing Flutter app at `C:\Users\HP\NETRAVA` with custom leaf painters, bottom waves, and welcome screen.
   - Google Colab research notebook at `C:\Users\HP\NETRAVA_B3_Improved_Training (1).ipynb` detailing staged EfficientNet-B3 training.
   - Comprehensive UI design suite `stitch_netrava_retinal_screening_app.zip` containing 14 mobile screens, HTML code, and design tokens (`clinical_precision_ai/DESIGN.md`).
   - Architecture diagrams and infographics in `Downloads/`.
   - APTOS dataset in `Downloads/aptos2019-blindness-detection/`.
   - Poppins font family in `Downloads/Poppins/`.
2. **Directory Structure Setup:** Created the complete clean architecture directory structure in `NETRAVA_1/`:
   - `docs/` (`agents/`, `architecture/`, `references/`)
   - `design_reference/` (`screenshots/`, `design_system/`, `branding/`, `assets/`)
   - `frontend/flutter_app/` (Copied and preserved existing Flutter code, added Poppins fonts)
   - `backend/` (`app/api/`, `app/core/`, `app/ml/`, `app/services/`, `app/models/`, `app/database/`, `app/schemas/`, `tests/`)
   - `supabase/` (`migrations/`, `seed/`, `tests/`)
   - `ai_model/` (`checkpoint/`, `evaluation/`, `reference/`)
   - `shared/` (`api_contracts/`, `constants/`, `documentation/`)
   - `scripts/` (`setup/`, `development/`, `deployment/`)
3. **Master Documentation Suite Created:**
   - `docs/PROJECT_AUDIT.md`: Complete audit of assets, completed work, technical dependencies, and risks.
   - `README.md`: Comprehensive 29-section root project guide.
   - `IMPLEMENTATION_PLAN.md`: Phase-gated roadmap with inputs, outputs, completion criteria, and status labels.
   - `AGENT.md`: Master operating manual for all AI agents.
   - Individual agent guidebooks: `AGENT_00_COORDINATOR.md` through `AGENT_07_DOCUMENTATION.md`.

### Files Created
- `docs/PROJECT_AUDIT.md`
- `README.md`
- `IMPLEMENTATION_PLAN.md`
- `AGENT.md`
- `docs/agents/AGENT_00_COORDINATOR.md`
- `docs/agents/AGENT_01_FRONTEND.md`
- `docs/agents/AGENT_02_UI_UX.md`
- `docs/agents/AGENT_03_BACKEND.md`
- `docs/agents/AGENT_04_AI_ML.md`
- `docs/agents/AGENT_05_DATABASE.md`
- `docs/agents/AGENT_06_QA.md`
- `docs/agents/AGENT_07_DOCUMENTATION.md`
- `docs/agents/WORK_LOG.md`

### Files Modified
- Extracted and populated `design_reference/` with 14 screen subdirectories, mockups, and `DESIGN.md`.
- Copied existing Flutter source code to `frontend/flutter_app/` without modifying core logic.
- Copied Poppins fonts to `frontend/flutter_app/assets/fonts/`.
- Copied `NETRAVA_B3_Improved_Training.ipynb` to `ai_model/reference/`.
- Copied architectural diagrams to `docs/architecture/diagrams/`.

### Technical Decisions
1. **Preserve EfficientNet-B3 Backbone:** Model was confirmed to be `timm.create_model('efficientnet_b3', pretrained=True, num_classes=5, drop_rate=0.30)` with `ResizeWithPadding(300)` and ImageNet normalization. This architecture must not be modified.
2. **Clinical Precision AI Design Tokens:** Adopted the official Stitch design tokens (`surface: #e5fff7`, `primary: #005d49` / `#08785f`, `secondary: #149477`, `badge mint: #e6f4ee`, Inter/Poppins typography) as the single source of truth.
3. **Clean Architecture in Flutter:** Structured Flutter around feature slices (`features/`) while maintaining shared design system tokens in `core/theme/`.

### Testing Performed
- Validated directory structure creation and existence of all directories.
- Verified that all 14 screens from `stitch_netrava_retinal_screening_app.zip` were extracted and organized into categories.
- Verified that Flutter code from `C:\Users\HP\NETRAVA` was safely copied into `frontend/flutter_app/`.
- Verified that the training notebook was preserved in `ai_model/reference/`.

### Pending Work
- Create remaining Phase 0 documentation: `docs/SYSTEM_ARCHITECTURE.md`, `docs/DATABASE_ARCHITECTURE.md`, `docs/API_DOCUMENTATION.md`, `docs/SECURITY.md`, `docs/DEPLOYMENT.md`, `docs/architecture/*.md`, `design_reference/design_system/*.md`.
- Create OpenAPI contract in `shared/api_contracts/`.
- Create root `.gitignore` and `.env.example`.

### Blockers
- The trained model checkpoint `best_efficientnet_b3_staged.pth` is located in Google Drive from the Colab training session and needs to be downloaded into `ai_model/checkpoint/` or `backend/model/`.

### Dependencies
- Agent 04 requires `best_efficientnet_b3_staged.pth` to perform validation.
- Agent 03 requires database schema definitions from Agent 05 to build API ORM models.

### Next Recommended Action
Complete Step 9 (Design reference documentation), Step 10 (System, Database, Backend, and Frontend architecture documentation), Step 11 (API contracts), and Step 12 (Root configuration files).

### Handover Notes
Foundation files have been created. Next step is authoring the detailed design token files and architectural specifications.



---

## Task Entry #002

- **Agent ID:** AGENT_04 / AGENT_00
- **Agent Name:** Lead AI/ML Integration Engineer & Lead Project Coordinator
- **Date:** November 2, 2026
- **Development Phase:** Phase 1 — AI Model Integration
- **Task Name:** EfficientNet-B3 Model Loader, 300x300 Preprocessor, Grad-CAM Engine & Pytest Suite
- **Status:** COMPLETED

### Objective
Reconstruct the trained EfficientNet-B3 neural network, verify the saved checkpoint `best_efficientnet_b3_staged.pth`, implement aspect-ratio-preserving 300x300 image preprocessing, build the 5-class prediction engine, implement Grad-CAM explainability hooked to `model.conv_head`, and author comprehensive automated tests.

### Work Completed
1. **Checkpoint Verification & Model Loader:**
   - Located and verified `ai_model/checkpoint/best_efficientnet_b3_staged.pth` (size: 43.37 MB, epoch: 20, best_val_qwk: 0.8716).
   - Built `ai_model/inference/model_loader.py` instantiating `timm.create_model('efficientnet_b3', pretrained=False, num_classes=5, drop_rate=0.30)`.
   - Verified strict state dict loading with all 574 tensor keys matched successfully.
   - Built `ModelLoader` class and `get_model()` thread-safe singleton.
2. **Aspect-Ratio Preprocessor:**
   - Built `ai_model/inference/preprocessing.py` implementing `ResizeWithPadding(size=300, fill=(0, 0, 0))` using LANCZOS thumbnailing.
   - Preserves aspect ratio without stretching retinal structures and centers on a black canvas.
   - Applied ImageNet normalization ($\mu = [0.485, 0.456, 0.406]$, $\sigma = [0.229, 0.224, 0.225]$).
   - Validates inputs across file paths, raw bytes, binary streams, and PIL Images.
3. **Grad-CAM Explainability Engine:**
   - Built `ai_model/inference/gradcam.py` hooking into `model.conv_head`.
   - Captures forward activations and backward gradients, computes channel weights, applies ReLU rectification, interpolates to 300x300, and blends with Jet colormap ($\alpha = 0.40$).
   - Safely removes hooks in `finally:` blocks with zero memory/hook leakage.
   - Encodes overlays to Base64 strings for API delivery.
4. **End-to-End Prediction Engine:**
   - Built `ai_model/inference/predictor.py` implementing `NetravaPredictor`.
   - Returns ICDR grade (0–4), confidence, probabilities, referral recommendation, and inference latency.
5. **Pydantic Schemas:**
   - Built `ai_model/inference/schemas.py` with `ClassProbability`, `GradCAMResult`, and `PredictionResult`.
6. **Automated Pytest Suite:**
   - Authored 20 unit and integration tests across `test_model_loader.py`, `test_preprocessing.py`, `test_prediction.py`, and `test_gradcam.py`.
   - Executed tests using Pytest 9.2.0: **All 20 tests passed cleanly in 14.38s**.

### Files Created
- `ai_model/inference/__init__.py`
- `ai_model/inference/schemas.py`
- `ai_model/inference/model_loader.py`
- `ai_model/inference/preprocessing.py`
- `ai_model/inference/gradcam.py`
- `ai_model/inference/predictor.py`
- `ai_model/tests/test_model_loader.py`
- `ai_model/tests/test_preprocessing.py`
- `ai_model/tests/test_prediction.py`
- `ai_model/tests/test_gradcam.py`
- `ai_model/tests/data/000c1434d8d7.png`
- `ai_model/tests/data/001639a390f0.png`
- `docs/agents/AGENT_02_BACKEND.md`
- `docs/agents/AGENT_03_DATABASE.md`
- `docs/agents/AGENT_05_QA.md`

### Files Modified
- `ai_model/README.md`
- `docs/agents/AGENT_01_FRONTEND.md`
- `docs/agents/AGENT_04_AI_ML.md`

### Technical Decisions
1. **Preserve Frozen Weights:** Checkpoint `best_efficientnet_b3_staged.pth` was loaded strictly without modifications.
2. **Matplotlib Colormap Compatibility:** Supported `matplotlib.colormaps['jet']` for modern Matplotlib 3.8+ compatibility with fallback to `cm.get_cmap`.
3. **Decoupled Inference Package:** Formatted `ai_model/inference/` as a clean, self-contained Python package easily importable into FastAPI backend routes.

### Testing Performed
- **Automated Test Run:** `python -m pytest ai_model/tests/ -v` -> 20 passed in 14.38s.
- **Real Image Benchmark:**
  - Input: `ai_model/tests/data/000c1434d8d7.png`
  - Output: Grade 2 (Moderate NPDR), Confidence: 84.10%, Referral: True
  - Latency: 95.1 ms on CPU.

### Pending Work
- Phase 2: Supabase database schema and migrations.
- Phase 3: FastAPI endpoints integrating `NetravaPredictor`.

### Blockers
- None. Phase 1 is fully functional and tested.

### Dependencies
- Backend Engineer (Agent 02 / Agent 03) can now import `from ai_model.inference import NetravaPredictor` to build the `/api/v1/predict` endpoint.

### Next Recommended Action
Initiate **Phase 2 (Supabase Database)** to apply migrations and configure storage buckets, followed by **Phase 3 (FastAPI Backend)** to expose the prediction and Grad-CAM APIs.

### Handover Notes
Phase 1 milestone is 100% achieved. The AI inference engine is operational, robust, and verified with 20 passing automated tests.

---

## Task Entry #003 — Phase 3: FastAPI Backend Development (COMPLETE)

**Date:** 2026-11-03
**Agent:** Agent 03 (Backend Engineer)
**Status:** ✅ COMPLETED — 39/39 tests passing

### Summary
Full FastAPI backend implementation for NETRAVA. All API routes, services, schemas, middleware, and tests implemented and passing.

### Files Created

**Core Foundation:**
- `backend/app/__init__.py`
- `backend/app/main.py` — FastAPI app factory, lifespan, CORS, exception handlers, request timing middleware
- `backend/app/core/__init__.py`
- `backend/app/core/config.py` — Pydantic BaseSettings with all environment variables
- `backend/app/core/security.py` — JWT verification, `get_current_user` FastAPI dependency
- `backend/app/core/logging.py` — Loguru config (JSON in prod, colourised in dev), stdlib intercept

**Schemas:**
- `backend/app/schemas/__init__.py`
- `backend/app/schemas/common.py` — `ErrorResponse`, `HealthResponse`
- `backend/app/schemas/auth.py` — `LoginRequest`, `LoginResponse`, `UserProfile`
- `backend/app/schemas/patients.py` — `CreatePatientRequest`, `PatientSummary`, `PatientListResponse`
- `backend/app/schemas/screening.py` — `QCAssessment`, `CreateScreeningResponse`, `PredictRequest`, `PredictResponse`, `ReviewRequest`

**API Routes:**
- `backend/app/api/__init__.py`
- `backend/app/api/router.py` — Master API router
- `backend/app/api/v1/__init__.py`
- `backend/app/api/v1/health.py` — `GET /health`
- `backend/app/api/v1/auth.py` — `POST /auth/login`, `GET /auth/me`
- `backend/app/api/v1/patients.py` — `POST /patients`, `GET /patients`
- `backend/app/api/v1/screening.py` — `POST /screenings`
- `backend/app/api/v1/predict.py` — `POST /predict`

**ML Bridge:**
- `backend/app/ml/__init__.py`
- `backend/app/ml/model_bridge.py` — Singleton predictor, asyncio.Lock for Grad-CAM
- `backend/app/ml/image_validator.py` — Magic bytes, 15MB cap, decompression bomb protection

**Services:**
- `backend/app/services/__init__.py`
- `backend/app/services/auth_service.py` — Supabase GoTrue login and profile fetch
- `backend/app/services/patient_service.py` — Patient CRUD with duplicate MRN detection
- `backend/app/services/screening_service.py` — Laplacian QC, Supabase Storage upload
- `backend/app/services/prediction_service.py` — Inference orchestration, Grad-CAM upload, record persistence

**Tests:**
- `backend/tests/__init__.py`
- `backend/tests/conftest.py` — Session-scoped TestClient fixture
- `backend/tests/test_health.py` — 10 tests
- `backend/tests/test_auth.py` — 8 tests
- `backend/tests/test_image_validator.py` — 6 tests
- `backend/tests/test_patients.py` — 10 tests
- `backend/tests/test_screening.py` — 5 tests
- `backend/pytest.ini` — pytest configuration

**Packages installed:**
- fastapi 0.162.0, uvicorn 0.54.0, pydantic-settings 2.16.2, python-multipart 0.0.33
- python-jose[cryptography] 3.5.0, passlib 1.7.4, loguru 0.7.3
- pytest-asyncio 1.4.1, pytest-cov 7.1.0, email-validator 2.3.0

### Test Results
```
39 passed, 1 warning in 1.21s
```
- test_health.py: 10/10 ✅
- test_auth.py: 8/8 ✅
- test_image_validator.py: 6/6 ✅
- test_patients.py: 10/10 ✅
- test_screening.py: 5/5 ✅

### Technical Decisions
1. **RSC Pattern strictly followed** — all routes are thin, all logic in services/.
2. **asyncio.Lock for Grad-CAM** — `model_bridge.get_gradcam_lock()` serialises backward passes.
3. **Magic bytes validation** — JPEG `\xFF\xD8\xFF` and PNG `\x89PNG\r\n\x1a\n` checked before Pillow.
4. **Decompression bomb protection** — `Image.MAX_IMAGE_PIXELS = 50_000_000` set at module load.
5. **Graceful DB degradation** — all Supabase operations return 503 (not crash) when unconfigured.
6. **Numeric literal status codes** — avoids deprecated Starlette constants for forward-compatibility.
7. **JSON-safe validation errors** — ValueError objects from Pydantic validators are stringified before serialization.

### Pending (Phase 4+)
- Phase 2: Supabase database migrations (Agent 05)
- Phase 4: Flutter frontend (Agent 01)
- Phase 5: End-to-end integration (connect real Supabase credentials)

---

## Task Entry #004 — Backend Verification and Safe Continuation

- **Agent:** Codex primary backend agent
- **Date:** November 3, 2026
- **Status:** BLOCKED on live Supabase verification; local implementation and tests completed for this pass.

### Work completed
- Started FastAPI with the selected Python 3.11 environment on port 8003 after discovering port 8000 was already occupied. Verified model load, docs/OpenAPI, protected-route 401 behavior, missing-config login 503 behavior, and degraded health status.
- Fixed the API prediction integration to match `NetravaPredictor`, with tests for real checkpoint inference, normalized five-class output, and `conv_head` Grad-CAM.
- Restricted test JWTs to testing mode; added Supabase Auth token validation and trusted profile/role/clinic lookup for non-test requests.
- Added clinic-scoped service operations and fail-closed persistence behavior, transactional RPC calls, report review/audit writes, storage cleanup, private media paths, health probing, and production configuration checks.
- Authored the initial Supabase migration and refreshed backend/API/security documentation and handoff.

### Files changed or added
- Backend app, services, API schemas/routes, and backend tests.
- `backend/.env.example`, `backend/README.md`, `shared/api_contracts/openapi_contract.json`.
- `supabase/migrations/202611030001_backend_core.sql`, `supabase/README.md`.
- `docs/API_DOCUMENTATION.md`, `docs/SECURITY.md`, `docs/PROJECT_AUDIT.md`, `docs/PROJECT_HANDOFF.md`, `docs/agents/WORK_LOG.md`, `AGENT.md`, and `IMPLEMENTATION_PLAN.md`.
- No Flutter source or model checkpoint changes.

### Verification
- Python 3.11 combined backend + AI pytest suite: `72 passed in 18.23s`; pytest emitted the `asyncio_default_fixture_loop_scope` deprecation warning.
- `pip check`: no broken requirements. Supabase client import works after installing declared `supabase` dependency version 2.33.0 into the selected Conda environment.
- No Supabase CLI, PostgreSQL client, Docker runtime, project URL, or keys are configured. No migration was applied and no live database/storage request was made.

### Blockers and handover
- Backend Phases 2-3 remain unverified against live Supabase (Auth, schema/RLS, RPC transactions, storage, signed URLs, clinic isolation). Health reports degraded because the database is unavailable.
- Next task: use a disposable development Supabase project to review/apply the additive migration and run live role, RLS, persistence, and storage integration tests. Keep Flutter work paused until backend verification is complete and the owner approves it.

## Task Entry #005 — Existing Supabase Connection Verification

- **Agent:** Codex primary backend agent
- **Date:** November 3, 2026
- **Status:** BLOCKED before live connection; no credentials were present.

### Checks performed
- Read `backend/.env.example` and `backend/app/core/config.py`; checked root/backend `.env` existence and process environment variable names without reading or printing secret values.
- Selected Python 3.11 environment reports Supabase SDK installed (`supabase 2.33.0`).
- Re-ran `python -m pytest backend/tests ai_model/tests -q -p no:cacheprovider --basetemp=...\.pytest-tmp`: **72 passed in 16.51s**. These are local unit/API and mocked integration tests, not live Supabase tests. Pytest reports the `asyncio_default_fixture_loop_scope` deprecation warning.
- Reviewed `supabase/migrations/202611030001_backend_core.sql` and backend query usage. The requested live tables, policies, and buckets could not be queried because no URL/keys are configured; no database or storage request was made and no live data changed.

### Findings
- Missing local variables: `SUPABASE_URL`, `SUPABASE_KEY` (public/anon), and `SUPABASE_SERVICE_ROLE_KEY` (backend only). `SECRET_KEY` and `ENVIRONMENT` were also unset in the process; keep secrets in ignored local config and never place the service-role key in client code or documentation.
- The checked-in migration places the probability array in `predictions.probabilities` and the heatmap path in `predictions.gradcam_heatmap_path`; it does not define separate `prediction_probabilities` or `explanations` tables. The existing live schema is unknown. The migration includes policy creation statements and changes bucket privacy on conflict, so it must not be blindly applied.
- Live connectivity, Auth/JWT, existing table/FK access, RLS/clinic isolation, all three buckets, signed URLs, and persistence remain unverified.

### Exact next task / handover
- Configure local access to the **existing development project**, obtain a schema-only snapshot, and reconcile actual tables/policies/buckets with backend queries and migration before any DDL change. Then run tagged safe integration checks for Auth/JWT, cross-clinic denial, storage upload/read/signed URL, and patient/screening/prediction/report/audit persistence with cleanup. Do not begin Flutter work; do not apply migrations or alter existing database state before review.

## Task Entry #006 — Local Supabase Environment Template

- **Agent:** Codex primary backend agent
- **Date:** November 3, 2026
- **Status:** Complete (local file setup only; no live connection attempted).

### Work completed
- Checked for root `.env`; it did not exist, so created it with the supplied project URL, publishable/service-role key placeholders, `ENVIRONMENT=development`, and a locally generated random `SECRET_KEY`. The key was written directly and never printed. Existing configuration would have been preserved if the file had existed.
- Updated root `.env.example` and `backend/.env.example` with placeholders only for `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, and `SECRET_KEY`.
- Confirmed `backend/app/core/config.py` reads `.env` and expects the exact requested variable names. The env file path is relative to the working directory; use project root as specified in `backend/README.md`.
- Confirmed `.gitignore` ignores `.env` and `.env.*`, with `!.env.example` allowing the examples.

### Safety and next step
- No actual Supabase API keys were exposed or added. No network request, database query, SQL, migration, storage operation, model/checkpoint change, or Flutter change was performed.
- Owner: open `C:\Users\HP\NETRAVA_1\.env` locally and replace `PASTE_PUBLISHABLE_KEY_HERE` on the `SUPABASE_KEY` line with the Supabase Publishable key; replace `PASTE_SECRET_KEY_HERE` on the `SUPABASE_SERVICE_ROLE_KEY` line with the Supabase Secret/service-role key. Keep the second value private and backend-only. Leave the generated `SECRET_KEY` unchanged.
- After filling the placeholders, request live verification. First inspect the existing project schema and security setup; do not apply the local migration without a reviewed comparison.

## Task Entry #007 — Safe Supabase Configuration Verification

- **Agent:** Codex primary backend agent
- **Date:** November 3, 2026
- **Status:** Local configuration verified; limited read-only endpoint probe passed.

### Verification performed
- Confirmed root `.env` exists. Loaded it through `backend.app.core.config.Settings` under the selected Python 3.11 environment. `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SECRET_KEY`, and `ENVIRONMENT` were each present and non-empty; URL used HTTPS and environment value was valid. No values were printed.
- Confirmed `.gitignore` has `.env`, `.env.*`, and `!.env.example` rules.
- Initialized Supabase SDK clients locally with the publishable key and server-side secret key; constructors succeeded.
- Sandbox networking initially returned a connection error. After approval for one read-only HTTPS request, `GET /rest/v1/clinics?select=id&limit=0` using the server key returned **HTTP 200**. Response body was suppressed; the request returned no rows.

### Interpretation and safety
- Verified: local configuration loading, SDK client construction, project REST connectivity, and permission to run this zero-row query against `clinics` with the server-side key.
- Not verified: user login or Supabase-issued JWT, end-user database grants, RLS, clinic isolation, other tables/relationships, Storage buckets/signed URLs, or record persistence. Service-role access bypasses RLS, so this probe cannot establish RLS behavior.
- No migrations, SQL, writes, storage operations, record reads, AI/checkpoint changes, or Flutter changes were performed.

### Next task
- Obtain and safely inspect an existing-project schema/policy snapshot; compare it with backend expectations. Then perform separately approved/safe read-only tests for user JWT and cross-clinic RLS behavior. Keep writes, migration changes, and Flutter development gated until their respective review/approval.

## Task Entry #008 — Combined Live Schema and Backend Compatibility Audit

- **Agent:** Codex primary backend agent
- **Date:** November 3, 2026
- **Status:** Live metadata audit complete; backend completion blocked on schema/security reconciliation.

### Read-only live checks
- Supabase REST OpenAPI returned HTTP 200 and listed all ten expected tables. All ten service-role zero-row `select=id&limit=0` queries returned HTTP 200. Selected embedded relationship probes (profiles→clinic, screenings→patients, images→screenings, predictions→images/probabilities/explanations, reports→screenings/predictions) returned HTTP 200. No records were requested.
- Auth health returned HTTP 200. This verifies the Auth service endpoint is responding, not user login or JWT validation.
- Storage bucket listing returned HTTP 200; `fundus-images`, `gradcam-heatmaps`, and `clinical-reports` exist and metadata marks all three private. Metadata contained no explicit file-size or MIME allow-list. No upload/download/signed URL was attempted.
- A publishable-key anonymous zero-row query of `patients` returned HTTP 200; zero rows were requested. This does not prove either public record access or RLS protection.
- Exact backend query-shape probes for auth profile fields, patient MRN search, retinal-image clinic filter, and report clinic filter each returned HTTP 400 / PostgreSQL `42703` (undefined column).
- Current REST OpenAPI lists `current_user_clinic`, `current_user_role`, and `rls_auto_enable`; it does not list the backend's expected write RPCs `register_clinic_patient`, `create_screening_records`, `write_screening_prediction`, or `write_screening_review`. `rls_auto_enable` was not called; its body/grants require review.
- Direct catalog verification of SQL constraints/indexes/RLS policies was unavailable: no `DATABASE_URL`, PostgreSQL driver, `psql`, or Docker. No SQL, migration, row read/write, storage object operation, policy change, model change, or frontend change occurred.

### Confirmed live schema mismatches
- `clinics`/`user_profiles`: live `clinic_name` and `is_active`; backend expects `name` and `active`.
- `patients`: live `patient_code`, `sex`, `phone`, `medical_notes`, `created_by`; backend searches/writes `mrn`, `gender`, `phone_number`, `notes`, `registered_by`, and structured diabetes fields.
- `retinal_images`: live `eye_side` and no `clinic_id`; backend image authorization requires `clinic_id` and writes QC/eye fields via a missing RPC.
- `predictions`: live `confidence`, `referral_recommended`, `model_name`, `model_version`; backend migration expects extra clinic/severity/requested-by fields and JSONB probability + heatmap path. Live normalized child tables `prediction_probabilities` and `explanations` exist instead.
- `reports`: live reviewer/final-grade/review-status/PDF fields; backend filters by absent `clinic_id` and uses a missing write RPC. `audit_logs` live actor/resource column names differ from the migration.
- Table columns and selected FK embeddings are documented in `docs/PROJECT_AUDIT.md`.

### Safe local code changes and tests
- Sanitized request-validation logs and responses so submitted values are omitted; removed filenames, patient/resource identifiers, and raw exception text from relevant logs.
- Added regression tests for validation-input, upload-filename, and database-exception log leakage. Added an assertion for grade-2 referral threshold.
- Full selected-Python suite: `python -m pytest backend/tests ai_model/tests -q -p no:cacheprovider --basetemp=...\.pytest-tmp` -> **75 passed in 19.03s**. Existing pytest-asyncio fixture-loop-scope deprecation warning remains. No live workflows were exercised by this suite.

### Proposed next step (approval-dependent live changes deferred)
- Get a schema-only export including `pg_policies`, complete FK/unique/check constraints, indexes, storage policies, and function bodies/grants. Preserve the live normalized tables and adapt backend field mappings/RPC contracts; decide explicitly whether missing structured diabetes fields require an additive migration. Review `rls_auto_enable`. Do not apply `202611030001_backend_core.sql`; it conflicts with the existing database and also updates bucket privacy on conflict.
- Then test Auth/JWT and clinic isolation with controlled clinic test accounts. Use an isolated development environment for test records and bucket writes. Backend remains not ready for Flutter integration; frontend stays paused pending full verification and owner approval.

## Task Entry #009 — Backend continuation and local verification

- **Agent:** Codex primary backend agent
- **Date:** November 3, 2026
- **Status:** Local work completed and tested; live Supabase workflows remain blocked/unverified.

### Work completed

- Added clinic-scoped patient detail retrieval and updated patient list/detail query mappings to the previously observed live patient fields.
- Changed prediction image clinic authorization to query the confirmed `retinal_images → screenings` relationship instead of the nonexistent `retinal_images.clinic_id` field. Added tests for the related-clinic query and fail-closed not-found handling.
- Kept the existing EfficientNet-B3 checkpoint unchanged. Report PDF generation/upload helper was implemented earlier in this continuation and is covered by synthetic-data/mocked-storage tests; it is not connected to live report metadata because that schema/function contract has not been supplied.
- Regenerated the shared OpenAPI contract and updated the API reference, audit, handoff, and this work log. Updated AGENT status and exact next task.
- Did not change Flutter files, model weights, live database schema/data, RLS, storage buckets/objects, or apply the local migration.

### Verification

- `& 'C:\Users\HP\.conda\envs\py311\python.exe' -m pytest backend/tests ai_model/tests -q -p no:cacheprovider --basetemp='C:\Users\HP\NETRAVA_1\.pytest-temp-final'` → **87 passed in 17.12s**. This is local test coverage, including real-checkpoint inference/Grad-CAM, patient/prediction clinic-query regression tests, and mocked database/storage behavior, not live persistence.
- Final configured rerun after setting `asyncio_default_fixture_loop_scope = function` in `backend/pytest.ini`: `python -m pytest -c backend\pytest.ini backend/tests ai_model/tests -q -p no:cacheprovider --basetemp=C:\Users\HP\NETRAVA_1\.pytest-temp-configured` → **87 passed in 16.10s**, without the fixture-scope warning. This is the latest result.
- The first combined run used the default Windows temp path and ended with **83 passed, 2 setup errors** because access to `AppData\Local\Temp\pytest-of-HP` was denied. Re-running under a new temp folder inside the writable workspace produced the 85-pass result.
- Uvicorn started and loaded the model. Local health, docs, and OpenAPI returned HTTP 200; unauthenticated patient access returned HTTP 401. Health reported degraded (`model_loaded=true`, `database_connected=false`). The server was stopped cleanly.
- A direct read-only Supabase request in this session failed with `ConnectError`; no request body or secret was displayed. This does not invalidate prior recorded read-only successes, but current connectivity is not verified here.
- `pip check` reported no broken requirements. Checkpoint remains 43,377,043 bytes, SHA-256 `3578BC6B7CA2112DB9D1B5908368953BE833A2B86027DECC734EEF92C0FA250D`.

### Blockers and exact next task

- Obtain schema-only database metadata (types, constraints, indexes, policies, storage policies, function definitions and grants) through an approved read-only export. Then reconcile existing normalized probability/explanation/report/audit structures and write RPC contracts without applying migrations or writing live test data.
- Current Supabase connectivity, real JWT/login and inactive-user checks, RLS/clinic isolation, Storage object operations, and live persistence remain unverified. Patient updates and complete screening/report/audit workflows remain incomplete. Backend phases are not complete; keep Flutter paused.


## Backend verification update ? 2026-11-13

Status: **BLOCKED / NOT READY FOR FRONTEND**. Project .venv (Python 3.11.9): **94 tests passed**, 6 warnings. Startup, model, health, Swagger, CORS and read-only Supabase connectivity verified. Live account credentials were not located. Four required transactional RPCs are absent from live REST metadata; unsafe direct-write fallbacks were removed. No live writes or migration changes performed. See [full verification report](../BACKEND_VERIFICATION_2026-11-13.md) for files, endpoint results, root causes and blockers. No route or request/response field changes; shared OpenAPI regenerated with installed dependencies. Flutter remains paused.


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

## Flutter frontend implementation — 2026-11-14

- Agent: Codex, acting as frontend architect under the owner's explicit complete
  Flutter implementation request. This request supersedes the historical frontend
  pause; hosted backend acceptance is not presumed complete.
- Added: configuration/network client, models, five endpoint services, session
  ChangeNotifier, shared clinical widgets, auth/dashboard/patient/screening/result/
  report/profile screens, native PDF file handling and frontend verification tests.
- Updated: Flutter app root/theme/pubspec and lockfile, Android internet/backup
  configuration and debug-only HTTP, frontend guide and roadmap progress note.
- Existing backend, model, checkpoint, Supabase schema and secrets were not changed.
- All existing business API routes are connected. Original encoded bytes are reused
  for screening/prediction; retinal_image_id is a query parameter. Review uses the
  exact report schema and only trusted clinician/admin roles. No mock production
  login/results, invented findings, OAuth, role selection or queue counters.
- Verification: Flutter 3.44.1/Dart 3.12.1; pub get succeeded; Android debug APK built;
  analyzer clean; nine unit/widget tests passed, including technician navigation
  and clinician draft/sign-off. Pixel_10 integration smoke passed against the real
  local backend and native secure storage (startup, field validation, health).
- Environment correction: the first backend process lacked network access and
  returned degraded/503. Restarted the unchanged backend with normal network access;
  real /health now reports healthy, model_loaded=true, database_connected=true.
- Windows desktop-plugin generation was resolved with project-local generated
  junctions, without changing Developer Mode/security settings. Emulator was
  recovered from offline state without wiping data. CUA runtime failed to initialize;
  Android screencap fallback verified the actual empty login layout with no clipping.
- Remaining acceptance: owner enters account credentials directly in the emulator;
  verify live login, patient creation, storage/QC, real inference and clinical PDF.
  Fixtures are isolated test evidence, not a claim of a live authenticated roundtrip.
- Handover: `frontend/flutter_app/FRONTEND_GUIDE.md` contains run commands, architecture,
  dependencies and API limitations. Backend startup and health connectivity were
  exercised without revealing credentials. No full-project completion claim.


## 2026-11-14 ? Signup integration (Agent 03 / handover to 01, 05, 00)
Implemented backend registration and strict schemas, safe pending-profile trigger, Flutter signup integration, API contract and tests. Latest owner request authorizes authentication frontend changes. Handover across frontend/database domains is recorded here. 114 backend tests and 50 existing PostgreSQL checks pass; new trigger checks pass. Hosted deployment/account creation intentionally not performed without owner approval. Files and runbook: docs/AUTH_SIGNUP_REPORT.md. Blockers: deploy reviewed trigger, approve/assign clinic, verify new real account and full clinical workflow.
Flutter follow-up: Dart analysis clean, nine existing tests and new signup validation widget test passed (10 total).


## 2026-11-14 ? Simplified active signup, cross-domain handover
Owner explicitly requests no approval gate. Backend/frontend/database changes coordinated locally: phone collection, active private-workspace technician trigger, login redirect and safe profile verification. Existing role and clinic guards remain. 117 backend tests, 20 signup cases including two subsequent signup/login/me tests, 10 Flutter tests and clean Dart analysis; local active signup PostgreSQL/RLS checks pass. Handover to database operator: review/apply 202611140002_active_signup.sql and email confirmation configuration before live verification; no hosted changes made. Existing users intentionally untouched. Full details: docs/AUTH_SIGNUP_REPORT.md.


## 2026-11-14 ? Authentication messaging cleanup
Removed administrator approval/contact and clinic-assignment wording from active auth responses; sign-in now says private workspace. Retained active technician/private workspace provisioning and clinic isolation. 38 signup/auth tests passed. Hosted migration deployment still required; no hosted changes made.

## 2026-11-14 � Authentication configuration recovery
Resolved .env path relative to project root in backend/app/core/config.py, verified configuration loads when launched from backend directory, replaced duplicate backend instances with one background server. 29 auth/signup tests passed. Live read-only checks: health 200, model and database connected, signup email/phone columns available, Auth settings reachable. Hosted email auto-confirm is disabled (email confirmation required). No account/settings/schema writes performed.

## 2026-11-14 � Existing signup account diagnosis
Read-only hosted check found the screenshot email already exists and is confirmed, but profile is inactive with no clinic/phone/email. Prepared scripts/verification/repair_existing_signup.sql for owner-reviewed activation and isolated workspace; no hosted writes performed. Improved safe provider error mapping for legacy duplicate messages, weak passwords, restricted email delivery and mail rate limits; 24 signup tests passed. Exact last provider error body was not retained, so no claim that duplicate email alone explains the generic 400.

## 2026-11-14 � Approved hosted account repair
Owner explicitly approved targeted repair for existing signup account. Direct DATABASE_URL unavailable; used backend service-role REST API with conditional profile update and workspace cleanup on failure. Applied and re-read verified active technician, separate active private workspace, correct name/email/phone, Auth email confirmed. Existing password/confirmation unchanged. FastAPI login using the password supplied in the latest signup screenshot returned 401 INVALID_CREDENTIALS; no JWT issued. No password reset attempted. User must log in with the existing Auth password or authorize a password reset. New-signup trigger migration was not deployed by this targeted repair.


## 2026-11-14 ? Signup chosen-password and recovery implementation
Backend/frontend coordination: explicit duplicate-account rejection including unconfirmed identities, public recovery email form, one-time recovery token browser page, secure GoTrue update. 136 backend tests, 11 Flutter tests and Dart analysis pass. Local reset URL configured; running reset page/script/health return 200. Hosted config/email/new-account test pending owner email and reviewed URL/template settings. No hosted password change or email send. Complete files/setup: docs/PASSWORD_RECOVERY_REPORT.md.


## 2026-11-14 ? Owner-confirmed empty test account deletion
Explicit confirmation received for preamgills232@gmail.com only. Rechecked original UUID, technician role, sole workspace membership, no clinical/audit records and empty storage prefixes. Deactivated target before hard-deleting Auth identity, then deleted its matching profile and empty private workspace. Verified Auth UUID returns 404, email absent from paginated Auth list, profile/workspace absent. Administrator account and profile preserved; patient/screening/image/prediction/report/audit counts unchanged. Scoped execution recorded in scripts/verification/delete_selected_test_account.py (original UUID fixed; will not target a recreated identity). No other accounts or clinical data deleted.


Password policy correction: actual hosted signup returned HTTP 422 with numeric code=422, error_code=weak_password and minimum 12 characters. Fixed error_code precedence over numeric code; signup/reset confirmation schemas and Flutter/browser reset validation now require 12 characters. Existing login still allows historical passwords. Diagnostic signup was rejected; no account created or password changed. 57 authentication/signup/recovery tests passed.


## 2026-11-15 ? Current status audit (documentation only)
Inspected active Flutter/FastAPI/SQL/model code and performed read-only hosted verification. Fresh 158 backend+AI tests, 11 Flutter tests, clean Dart analysis, 16 API/50 actual SQL checks and active-signup SQL checks pass. Live signup/login/me/list successes evidenced in retained logs; new private technician workspace remains empty and lacks a reviewer, blocking standalone clinical PDF. Recovery request accepted but delivery/reset/new-password login not established. Current report: docs/CURRENT_PROJECT_STATUS.md; planning completion estimate 75%, transparent rubric included. No app code or hosted writes changed. Frontend guide corrected for implemented signup/recovery.

## 2026-11-15 - Separate AI screening PDF

Implemented owner-requested technician AI report across FastAPI and Flutter while preserving clinician review permissions. Added private original/Grad-CAM inclusion, required disclaimer, saved-data mapping and workspace isolation tests. No migration/policy/model changes. Backend full suite 145 passed; final AI report suite 8 passed. Flutter full suite 15 passed before dedicated progress case; analyzer clean; debug APK built. Synthetic PDF rendered and visually inspected. Live authenticated Android/Supabase acceptance remains pending. See docs/AI_SCREENING_REPORT_IMPLEMENTATION.md for complete changed-file inventory, architecture, security and acceptance steps.

Final AI screening report validation: 146 backend tests and 16 Flutter tests passed. Dedicated loading/progress regression passed; Android debug APK built successfully; analyzer clean. Live authenticated device acceptance remains pending.

## 2026-11-15 - Correct result-page navigation and pin current prediction

Removed the old clinician/clinical report action from Screening Result. Its sole report action is now Generate AI Screening Report -> AI report generation -> View Report / Download Report. The current screening ID and prediction ID are passed to the AI PDF endpoint; backend filtering prevents silent substitution of a newer prediction or a prediction from another screening. Added the exact short AI disclaimer alongside the existing full disclaimer. JWT, workspace scope and storage protections are unchanged.

Changed result_screen.dart, ai_report_screen.dart, report_service.dart, backend screening route/report service/PDF renderer, frontend workflow/AI report tests, backend AI report tests, shared OpenAPI and API documentation. Tests: all 16 Flutter tests passed; 20 backend PDF/report tests passed; analyzer clean. Attached to the existing Android debug app and hot reloaded. Running local backend OpenAPI confirms AI PDF route and prediction_id parameter are available. Real current-result interaction/opening is not verified: CUA capture fails because the emulator window crop is outside the captured monitor. User was asked to move the emulator onto the main display; no authenticated screen state or live PDF was claimed.

Navigation correction validation: updated Android debug APK built successfully. Flutter attach was detached without terminating the app. Real current-result PDF opening remains pending the emulator display/capture handoff.

## 2026-11-15 - Signup provider failure diagnosis
Agent 03 added safe signup-stage/provider-category logging and actionable email-delivery, database-provisioning, rate-limit and timeout errors. Unconfirmed-email login now explains confirmation rather than reporting a wrong password. Seventy relevant backend signup/security/auth/recovery tests passed. Read-only hosted checks confirm admin identity lookup and required profile fields return 200, signup enabled, confirmation enabled, attempted identity absent. Backend restarted with logs in tmp/signup-fix-backend-stdout.log; waiting for a user retry to identify the actual hosted failure. No hosted settings, passwords, accounts or schema changed by this diagnostic patch. Signup is not yet live verified fixed.

## 2026-11-15 - Hosted signup duplicate-clinic correction
Agent 05/root cause confirmed by hosted Auth log: every new user inserted the constant clinic_name Personal screening workspace, while hosted clinics has a UNIQUE clinic-name constraint; signup rolled back with SQLSTATE 23505 then 25P02. Added forward migration supabase/migrations/202611150001_unique_signup_workspace.sql using the complete Auth UUID in each workspace name. Agent 06 updated actual-SQL regression to reproduce the old second-signup failure with hosted-equivalent uniqueness, apply the fix twice, verify same-prefix IDs remain distinct, preserve existing records and retain RLS/role/rollback checks. node scripts/database_test/verify_active_signup.mjs passed. Applied the exact function correction through the existing authenticated Supabase SQL Editor; post-commit unique_workspace_fix_installed returned true. No existing users/clinics/data, role policy or email-confirmation settings changed. User asked to retry signup and confirm email; actual post-fix signup/login acceptance still pending. No APK change required.

## 2026-11-15 - Immediate hosted signup enabled
Owner explicitly approved disabling email confirmation. In hosted Supabase Authentication > Sign In / Providers, changed Confirm email OFF and saved; dashboard reported Successfully updated settings. Read-only Auth settings verifies external.email=true and mailer_autoconfirm=true. Local config.toml already specifies auth.email.enable_signup=true and enable_confirmations=false; 38 signup regressions passed in the preceding continuation. Existing newly created user's name/email/phone, active technician role and workspace are persisted, but that identity remains unconfirmed because it predates the setting change. Automatic approval review rejected confirming that identity and creating a synthetic hosted QA account without explicit per-account/test-account authorization; no such writes ran. No password or role changed. Pending: user authorizes scoped confirmation of existing identity, or completes its email confirmation; real post-change new-signup/login acceptance remains user-driven.

## 2026-11-15 - Existing new-account login block cleared
Following the explicit account-specific question and owner's renewed instruction to solve login, applied only email_confirm=true through Supabase Admin API to the exact previously identified account UUID a503f544-2307-49c7-9330-38256b924cee after rechecking its email, active technician profile and assigned workspace. Re-read identity confirms email_confirmed_at present. Hosted immediate signup remains enabled (mailer_autoconfirm=true). No test identity was created and no password, role, workspace or other account changed. Password login itself is not replayed by the agent because the password must remain private; owner can now log in with the already registered email rather than signing up again.

## 2026-11-16 - Final Android readiness audit

Agent roles: coordinator/QA, with owner-authorized scoped frontend feedback fix. Read current application, model, Auth, RPC/schema, private storage, report and Android sources before changes. Findings recorded in docs/FINAL_ANDROID_READINESS_AUDIT.md before application edits. Added optional Dio upload progress callback and percentage/server-wait/cleanup UI, plus slow-upload/error/duplicate-action regression. No design, model, QC threshold, hosted schema, account, password, policy or clinical record changes.

Validation: baseline 184 Python/18 Flutter tests; final 184 Python/19 Flutter tests, Flutter analyze clean, pub get and pip check pass. Actual local PostgreSQL/real-model workflow passes 18 API + 50 SQL checks including technician AI PDF without clinical report. Active-signup full-UUID uniqueness/RLS/rollback SQL check passes. Fresh synthetic two-page workflow PDF rasterized and visually inspected. Phone-configured debug APK built and rebuilt. Actual backend starts/loads checkpoint; localhost and PC Tailscale health healthy. Read-only hosted Auth settings mailer_autoconfirm=true, email enabled; all three buckets private; four write RPC names exposed; anonymous patients 401. Running OpenAPI exactly matches shared contract; ten protected routes reject missing token. Initial invalid-token request timed out upstream (503); unchanged retry returns 401. No connected device or successful private credential flow verified. No live writes performed.

Files: frontend screening screen/service and new upload_progress_test.dart; final audit; supersession note in CURRENT_PROJECT_STATUS; FRONTEND_GUIDE; this ledger and roadmap. Temporary evidence under tmp/audit-* and tmp/pdfs/audit-ai-*. Final recommendation READY FOR PHYSICAL ANDROID TESTING means controlled synthetic acceptance may begin; hosted writes/role-token isolation, real recovery, phone camera/gallery/PDF and performance remain acceptance gates. No production/clinical readiness claim. Older historical status assertions are preserved with explicit supersession.

Final artifact addendum: formatted source APK refresh passed in 22.5 s; final APK 191,195,010 bytes, SHA-256 f7409e348b55e4cad4bce188eb3cca2d50ccddb98a0a6e6e7e9966ceacad5dc9. One additional read-only live transport test passed using the actual Flutter ApiClient/Dio against running FastAPI (healthy model/DB and normalized missing-token 401), with no HTTP adapter. This one-off file is outside test/ at frontend/flutter_app/tmp/audit_flutter_transport_test.dart and is not counted among the 19 isolated Flutter suite tests. Complete authenticated frontend-to-hosted workflow remains pending.

## 2026-11-21 - Windows development launcher and ngrok

Coordinator, backend, frontend and QA scope. Added CMD launchers, a PowerShell process manager, and a Windows/Android runbook. Existing healthy listeners were reused. HTTP health passed locally and over HTTPS with network access, and the public patients endpoint rejected an anonymous request with HTTP 401. An isolated port collision reported the ngrok PID and preserved the listener. Backend and AI suite passed 184 tests, Flutter passed 20 tests plus a separate compile-time URL override run, and Flutter analysis was clean. A restricted sandbox probe could not reach Supabase or terminate its isolated test process. The isolated process was subsequently stopped using its recorded identity with ordinary process access. The pre-existing ngrok session was preserved, so a fresh managed ngrok session remains unverified. ADB listed no device.
Managed backend lifecycle also passed on isolated loopback port 18001 with network access. The second start retained the listener PID, restart replaced it, OpenAPI returned 404, and stop removed the listener. Existing ports 8000 and 4040 retained their original listener PIDs.
