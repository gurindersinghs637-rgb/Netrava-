# NETRAVA final Android readiness audit

Audit date: 16 November 2026 (Asia/Calcutta).

## Findings recorded before application changes

The existing application already connects Flutter services to FastAPI, the trained
EfficientNet-B3 checkpoint, normalized database RPCs, private image storage and a
separate technician-accessible AI screening PDF endpoint. No redesign, model
replacement, schema deployment or account changes are required for the local audit.

Fresh baseline: 184 Python tests pass; 18 Flutter tests pass; Flutter analysis has
no issues; the phone-configured debug APK builds. Actual local PostgreSQL SQL and
real-model API workflow: 18 API checks and 50 SQL checks pass. Auth and Storage in
that workflow are controlled adapters, not hosted services.

Read-only hosted observations: Auth settings return mailer_autoconfirm=true and
email signup enabled; medical buckets are private; REST schema exposes the four
required write RPCs; anonymous patient access returns 401. This does not verify
deployed SQL function bodies, triggers, grants or authenticated workspace isolation.

Findings to address or retain as explicit limitations:

1. Upload has a busy spinner but no transferred-byte progress. Complete the
   existing upload feedback locally without changing its multipart contract.
2. No connected Android device: native camera/gallery, PDF viewer and frame timing
   cannot be accepted in this session.
3. No user credentials supplied: full hosted login-to-patient-to-PDF and two-user
   isolation remain unverified. Do not create accounts or medical records.
4. Quality control uses resolution-dependent Laplacian variance and brightness;
   it does not establish that the image is retinal or clinically gradable. Exposure
   is reported but does not itself reject an image. Preserve thresholds/model.
5. Screening/report history is session-only; no general screening retrieval/list
   endpoint or persistent history UI exists. Retained screening UUID supports PDF lookup.
6. Recovery inbox delivery, redirect allowlist and deployed template remain
   unverified. Local reset URL must be opened on its backend host.
7. Backend contains synchronous database/CPU work in async services; production
   concurrency, high-resolution memory use and startup frame warnings need measured
   acceptance. Existing inference executes in an executor with a Grad-CAM lock.
8. Historical documentation is stale about clinical-report dependency and email
   confirmation. Final evidence in this document supersedes those claims.

## Final recommendation

**READY FOR PHYSICAL ANDROID TESTING**

This is approval to begin controlled acceptance testing with synthetic patient data.
The required local test suites, real-model/local-SQL integration, backend startup,
PC-side Tailscale health and Android debug build pass. No critical local runtime
regression was reproduced. This does not certify clinical accuracy, production
security, successful hosted patient/Storage writes or successful native phone use.
Those acceptance checks are explicitly pending below. No device was connected.

Final APK: `frontend/flutter_app/build/app/outputs/flutter-apk/app-debug.apk`,
191,195,010 bytes (about 182.3 MiB). SHA-256:
`f7409e348b55e4cad4bce188eb3cca2d50ccddb98a0a6e6e7e9966ceacad5dc9`.

No accounts, passwords, confirmation settings, roles, live clinical records,
storage objects, policies or hosted schema were changed during this audit. The
trained checkpoint, architecture, preprocessing and quality thresholds are unchanged.

## Architecture and source inventory

| Area | Active implementation and findings |
|---|---|
| Flutter entry/navigation | `frontend/flutter_app/lib/main.dart` -> `app/app.dart` -> `screens/auth/session_gate.dart` -> login/dashboard. Root navigation returns to its first route when identity changes. |
| State/auth | `providers/session.dart`: ChangeNotifier dependency container, platform secure token storage, `/auth/me` restoration, logout/PDF cleanup, session-only screening/report references. No Riverpod dependency is required by this implementation. |
| HTTP | `core/config/api_config.dart` uses `String.fromEnvironment('API_BASE_URL')`; `core/network/api_client.dart` attaches Bearer tokens, normalizes JSON and binary PDF errors, uses 15-second connect, 90-second send and 3-minute receive limits, and does not automatically retry writes. |
| Screens | Active auth, patient list/intake/details, dashboard, screening/QC, prediction/Grad-CAM, AI report and separate clinical report, profile. Result navigation pins screening and prediction IDs. |
| FastAPI | `backend/app/main.py`, `api/router.py`, `api/v1/{auth,health,patients,screening,predict}.py`; schemas in `schemas/`; services in `services/`. Model warm-up occurs at startup. |
| Auth | GoTrue owns passwords and issues access JWTs. Production/development requests validate identity via GoTrue `/auth/v1/user`, then load trusted active role/workspace from PostgreSQL. Locally signed HS256 tokens are accepted only in the testing environment. |
| ML | `backend/app/ml/model_bridge.py` constructs `ai_model/inference/predictor.py`; actual PyTorch EfficientNet-B3 and conv_head Grad-CAM run in an executor, with a shared lock around inference/backpropagation. |
| Persistence | Auth identity -> `user_profiles` -> `clinics` (private workspace) -> `patients` -> `screenings` -> `retinal_images` -> `predictions` -> `prediction_probabilities` and `explanations`. `reports` records clinician reviews; `audit_logs` records mutations. |
| Storage | Private `fundus-images` and `gradcam-heatmaps`, clinic-prefixed paths and 30-minute signed URLs. AI PDF reads authorized private objects server-side. PDFs are generated on demand and returned as bytes; bucket existence does not prove PDF archival. |
| PDF | `services/report_service.py` authorizes and assembles persisted data; `report_pdf.py` validates and renders with ReportLab. `PdfFiles` saves to private temporary storage and opens through OpenFilex. |
| Database sources | Four forward migrations dated 20261113-20261115; the final full-UUID signup migration must follow the active-signup migration. Conflicting original schema is preserved under `supabase/legacy/`. |
| Contracts/docs | Running OpenAPI matches `shared/api_contracts/openapi_contract.json` exactly. Historical status documents contain superseded assertions; this dated audit records fresh evidence. |

No missing active imports, required checkpoint, declared font/logo asset or API
contract mismatch was found by the build, analyzer and tests. `backend/model/` is
a documented legacy location; the active checkpoint is under `ai_model/checkpoint/`.
Preserved `lib/app/routes.dart`, `screens/login_screen.dart` and welcome prototypes
are outside active SessionGate navigation; their placeholder OAuth controls do not
implement Google/Microsoft login. SQLAlchemy/Alembic/passlib dependencies are not the
active REST/RPC/Auth persistence path. They were not removed. There is no container
deployment acceptance result in this audit.

## Trained model verification

| Check | Result |
|---|---|
| Checkpoint | `ai_model/checkpoint/best_efficientnet_b3_staged.pth`, 43,377,043 bytes, present and loaded successfully |
| SHA-256 | `3578bc6b7ca2112db9d1b5908368953be833a2b86027decc734eef92c0fa250d` |
| Saved metadata | efficientnet_b3; input 300; epoch 20; seed 42; saved best validation QWK 0.8716031272631357. This is checkpoint metadata, not a fresh clinical validation result. |
| Architecture | `timm.create_model('efficientnet_b3', pretrained=False, num_classes=5, drop_rate=0.30)`; strict state-dict load and `(1,5)` output check |
| Preprocessing | RGB; aspect-preserving PIL LANCZOS thumbnail; centered black padding to 300x300; ImageNet mean `[0.485,0.456,0.406]`, std `[0.229,0.224,0.225]`; matches saved training notebook implementation |
| Classes | 0 No DR, 1 Mild, 2 Moderate, 3 Severe, 4 Proliferative DR; checkpoint mapping agrees |
| Device | Configured CPU; startup and real-checkpoint tests pass |
| Output/confidence | Five softmax probabilities; argmax grade and top-class probability. Output rounding is checked within SQL tolerance; confidence is not calibrated diagnostic certainty. |
| Explanation | Actual `conv_head` activations/backward gradients, normalized heatmap and blended PNG; hooks removed after generation. Tests exercise nonzero gradients. |
| Failure behavior | Missing/unloaded model -> 503; inference failure -> 500; persistence/storage errors surface. No dummy fallback exists in the active production path. |

The test suite includes real checkpoint inference and Grad-CAM. The local SQL/API
workflow also executed this model and saved five probability rows and an explanation.
It used the documented 400x266 derivative of the bundled authentic retinal image,
not a fabricated model response. Model test fixtures are not clinical validation.

`torch.load(..., weights_only=False)` assumes this repository's trusted local
checkpoint. Never substitute an untrusted downloaded pickle/checkpoint. No loader
security behavior was changed without approval.

## Upload, quality, storage and stability

Gallery and camera buttons invoke ImagePicker. The client validates JPEG/PNG magic
bytes and a 15 MiB size limit. Server validation reads at most limit+1 bytes, checks
signatures, verifies original encoded bytes with Pillow and decodes to RGB, with a
50-million-pixel cap. Corrupt/unsupported data returns 400, oversize returns 413,
and ungradable images return 422 with QC details. Camera capture uses the external
platform intent; no custom camera implementation or CAMERA permission is declared.
Native permissions/capture still need device testing.

`POST /screenings` checks patient/workspace ownership before storage, computes QC,
uploads original bytes privately, and creates screening/image/audit records through
a transaction. `/predict` checks the saved image relationship and original SHA-256,
so another patient/workspace or different image bytes cannot silently be analyzed
as that stored image. Prediction/probability/explanation writes are transactional.
Best-effort compensation exists for storage/database failures; interrupted network
operations can still require orphan inspection by an authorized operator.

The safe local change wires Dio's `onSendProgress` into the upload screen. It shows
the transferred percentage, then an explicit server-QC/save waiting state. Completion
and errors clear progress; repeated submission remains disabled. It does not infer
successful persistence from 100% upload progress. No multipart fields changed.

Important limitations:

- QC is a resolution-dependent blur/brightness heuristic, not a trained retinal
  detector. A sharp non-retinal image may pass. Under/overexposure is labelled but
  does not independently reject an image. The original bundled large image can
  fail sharpness while its documented thumbnail passes; do not lower the threshold
  or resize clinical inputs simply to make a demonstration pass. Calibrating QC
  needs a separately reviewed medical/quality change.
- Server decoding/QC and several synchronous Supabase calls execute in async service
  paths. Large images and concurrent requests can block other requests or increase
  memory. The 50-million-pixel cap still allows a large decoded allocation. No peak
  memory, load test or slow-network phone benchmark was measured here.
- The UI does not implement ImagePicker lost-data recovery after Android kills the
  activity during capture. Retest capture under low memory; a restart may require
  selecting the image again. No automatic recovery claim is made.
- There is no write idempotency key. An ambiguous timeout can follow a successful
  write. Do not repeatedly resubmit; retain references and check persisted state.
- No device/emulator was attached. No retained skipped-frame log was found in
  current `tmp`/`output` log searches. The warnings cannot be reproduced or assigned
  a measured cause. Startup restores secure storage and asynchronously checks the
  network; ML runs on the PC, not the Flutter UI thread. Profile a connected phone
  before optimizing. Debug startup warnings alone do not establish release jank.

## API and frontend compatibility

All paths below are under `/api/v1`. The running server's OpenAPI and saved shared
contract are identical. The active frontend calls these paths with compatible fields.

| Method/path | Caller/behavior | Verification |
|---|---|---|
| POST `/auth/signup` | Name/email/phone/password/confirmation; no client-selected role/workspace; 201 | Controlled Auth tests; local signup SQL; fresh successful hosted signup not replayed |
| POST `/auth/login` | GoTrue password login; trusted active profile; JWT response | Controlled Auth tests; successful hosted credentials not supplied |
| GET `/auth/me` | Session restoration/profile/role | Controlled tests; actual missing and invalid token 401 checks |
| POST `/auth/forgot-password` | Generic recovery acknowledgement | Local/provider-adapter tests; no email sent in this audit |
| GET/POST `/auth/reset-password` | Browser page and one-time recovery reset | Local tests; real inbox/token/password roundtrip pending |
| GET `/health` | Model and read-only DB probe | Actual localhost and PC Tailscale HTTP 200/healthy |
| POST `/patients` | Intake -> register_clinic_patient; 201; duplicate MRN 409 | Widget fixtures, backend tests and actual local SQL/API |
| GET `/patients` | Clinic-scoped search/page/limit | Fixture/backend tests; local API list; full live search/pagination pending |
| GET `/patients/{patient_id}` | Clinic-scoped detail | Fixture/backend tests and actual local SQL/API, cross-clinic 404 |
| POST `/screenings` | Multipart patient_id, OD/OS eye and original image; QC/storage; 201 | Fixture/backend and actual local SQL/API with controlled Storage |
| POST `/predict?retinal_image_id=...` | Same original bytes; real model, five probabilities, explanation and persisted ID | Fixture/backend plus real-model/local-SQL integration |
| GET `/screenings/{id}/ai-report/pdf?prediction_id=...` | Technician AI screening PDF; no clinical report required | Widget/backend plus real-model/local-SQL PDF; real phone open pending |
| POST `/screenings/{id}/report` | Clinician/admin review only; signed report immutable | Fixture/backend/local SQL; technician 403, signed edit 409 |
| GET `/screenings/{id}/report` and `/report/pdf` | Separate clinical report retrieval | Fixture/backend/local SQL; cross-clinic 404 |

There is no standalone screening GET/list endpoint or persisted history screen.
The current client holds upload/result data in memory, and can retrieve PDFs by a
retained screening UUID. A patient detail page is implemented; a historical screening
detail page is not. There is no profile/patient edit/delete, reviewer invitation,
OAuth or refresh-token workflow. These are identified limitations, not newly added
features. The result's AI PDF action does not call the older clinical endpoint.

Actual HTTP probes to ten protected routes returned 401 without a token. An
invalid-token `/auth/me` request initially returned 503 after a GoTrue ConnectTimeout;
an unchanged retry returned 401. The failed first assertion is retained in this
audit rather than counted as a successful Auth test. Provider outages are correctly
distinguished from bad credentials and fail closed, but network stability remains
an acceptance concern.

## Supabase, auth and database assessment

Fresh read-only hosted checks returned:

- Auth settings HTTP 200: `disable_signup=false`, email provider enabled,
  `mailer_autoconfirm=true`. New email signups currently do not require confirmation.
  Existing unconfirmed identities are not automatically repaired by this audit.
- REST clinic connectivity HTTP 200; expected ten application tables exposed.
- All four expected write RPC names exposed: register_clinic_patient,
  create_screening_records, write_screening_prediction, write_screening_review.
- Storage metadata HTTP 200: fundus-images, gradcam-heatmaps and clinical-reports
  all have `public=false`.
- Anonymous direct patient-table request HTTP 401.

No hosted schema/function/policy export or direct SQL connection was used. REST
metadata does not prove deployed constraints, trigger bodies, RPC grants or RLS
expressions. No hosted migrations were applied. Historical work logs record prior
deployment, but that is not fresh verification of deployed definitions.

Local migrations and actual PostgreSQL checks verify patient/screening/image/
prediction relationships, unique patient codes per clinic, unique probability grade
per prediction, one clinical report per screening, active-role checks, transaction
rollback and restrictive workspace read boundaries. Write RPCs are service-role-only;
authenticated clients receive SELECT only. Storage policy blocks direct client
medical-media access; audit updates/deletes are revoked. Existing permissive policies
cannot bypass the added restrictive clinic boundary in the tested migration.

Not every identity/audit column has a database FK: for example the standalone schema
does not add a user_profiles.id -> auth.users.id FK, and actor IDs rely on trusted
Auth/active-profile checks in service RPCs. Some normalized tables retain nullable
clinic IDs or lack a created_at column. Those differences from the idealized AGENT.md
schema convention were preserved for existing-schema compatibility. Hosted FK/check
completeness is unverified; do not assume metadata exposure proves it.

The final signup migration names each private workspace using the full Auth UUID,
not a shared constant or truncated prefix. The fresh active-signup SQL regression
reproduces the old second-signup UNIQUE violation, applies the fix twice and tests
same-prefix UUIDs, preservation of existing rows, workspace isolation, role protection
and rollback. It passes. Existing disabled/pending accounts remain unchanged; do not
rerun earlier signup migrations after the final correction.

Passwords are sent only to GoTrue, absent from application profile persistence and
protected from validation-value logging. Login accepts existing 8+ character accounts;
new signup/reset requires 12+ characters. Logout is local token removal/PDF cleanup,
not global token revocation. Access-token expiry requires login; no automatic refresh.
Recovery uses a fixed backend redirect URL and a one-time token hash in a browser
fragment. The configured local reset page is unsuitable for an email opened on a
different device using 127.0.0.1. Hosted allowlist, SMTP and email-template deployment
were not available through the settings probe and remain unverified.

## AI PDF report acceptance

The local real-SQL/model workflow generated a technician AI PDF with an explicitly
pinned prediction ID and no row in `reports`. It returned `application/pdf`, valid
`%PDF-` bytes and `Cache-Control: no-store`. The AI route also sets nosniff.
Wrong-workspace and unrelated-prediction tests reject access.

Fresh output was rasterized with installed PyMuPDF (Poppler was not available) and
both pages inspected. The report contains the NETRAVA AI Screening Report title,
patient name/code/reference, screening date/time, original retinal image, predicted
grade, confidence percentage, all five probabilities, Grad-CAM and explanation,
generation timestamp and this exact disclaimer:

> This result is generated by an AI screening system and is intended to support screening and clinical decision-making. It is not a final medical diagnosis. A qualified healthcare professional should review the retinal images and findings before making a diagnosis or treatment decision.

No clipping or overlapping content was observed in this synthetic two-page report.
The screening status remains pending until clinical review; generating an AI report
does not sign off or complete a clinical screening. Missing original/Grad-CAM assets
are labelled unavailable. Missing saved probabilities are also explicitly labelled
for legacy records; a legacy incomplete record therefore cannot satisfy the full
five-probability acceptance requirement. Newly persisted predictions provide five
rows, verified by actual SQL. Invalid nonempty distributions are rejected.

Flutter validates the PDF signature, protects generation/open actions while busy,
shows errors for network/auth/ownership/not-found cases, and writes to private app
temporary storage. View Report and Download/Open Report both use the external PDF
viewer; this is not an in-app PDF renderer or an export to public Downloads. A
missing viewer produces an actionable message. Files are cleared on startup/logout;
copies retained by an external viewer are outside app control. Native open/save and
session cleanup need physical-device acceptance.

## Android and UI assessment

| Item | Evidence/result |
|---|---|
| SDK/toolchain | Installed Flutter 3.44.1 / Dart 3.12.1 used by build; Java 17 source/target; Android Gradle plugin 9.0.1 |
| Package | APK package/application ID `com.netrava.netrava`, label NETRAVA, version 1.0.0+1 |
| SDK levels | Final merged/build metadata: min 24, target 36, compile 36 |
| Networking | INTERNET permission; debug merge sets usesCleartextTraffic=true. No special network_security_config is required by the current debug HTTP configuration. Release requires an explicitly configured HTTPS API URL. |
| Phone configuration | Built with `--dart-define=API_BASE_URL=http://100.99.7.24:8000/api/v1`; string confirmed inside APK kernel asset |
| Emulator | Debug default remains `http://10.0.2.2:8000/api/v1`; phone build overrides it rather than editing source |
| Icon/splash | Custom icon, density variants and native pre-12/Android-12 splash resources exist; launcher artwork visually inspected. Platform splash rendering/cropping remains a phone check. |
| Fonts/design | Poppins files declared and theme uses Poppins; current cards/green design preserved |
| Native providers | Merged image-picker and OpenFilex FileProviders are non-exported and grant temporary URI permissions |
| Permissions | Merged plugins include legacy READ_EXTERNAL_STORAGE (max 32) plus READ_MEDIA_IMAGES/VIDEO/AUDIO. Review unnecessary broad media permissions before a production release; no permission policy changed in this audit. |
| Backup/signing | Backup disabled. Debug APK is debuggable. Release still inherits debug signing, so production distribution is not approved. |
| Secrets | No .env asset; no exact configured service-role key or backend SECRET_KEY found across uncompressed final APK entries. This exact-value scan is not a general binary security audit. |
| UI checks | Fixture widgets exercise forms, navigation, busy/errors, empty states, probabilities/Grad-CAM, report roles and logout. Scrollable bodies and wrapping identifier rows exist. All screen widths/text scales and device insets were not manually tested. |

## Tests executed and actual results

| Check | Actual result | Test boundary |
|---|---|---|
| `.venv\Scripts\python.exe -m pytest backend/tests ai_model/tests -q --basetemp=tmp/audit-pytest` | 184 passed, 7 summary warnings, 23.26 s | Baseline unit/API adapters plus real-checkpoint AI tests; extra cache-write warning due permissions |
| `.venv\Scripts\python.exe -m pytest backend/tests ai_model/tests -q -p no:cacheprovider --basetemp=tmp/audit-pytest-final` | 184 passed, 6 summary warnings, 21.46 s | Final full Python suite; no fresh coverage percentage measured |
| `flutter pub get` | Passed; 20 newer versions outside current constraints reported | Existing lockfile dependencies resolved; no upgrade requested |
| `flutter analyze` | No issues; baseline 5.9 s, after fix 6.4 s | Entire Flutter project static analysis |
| `flutter test` | Baseline 18 passed; final 19 passed | Unit/widget HTTP fixtures and mocked native services; not all-live E2E |
| `flutter test tmp/audit_flutter_transport_test.dart --dart-define=API_BASE_URL=http://127.0.0.1:8000/api/v1` | 1 passed | One-off actual Flutter ApiClient/Dio -> running FastAPI HTTP: healthy model/DB and normalized missing-token 401. No HTTP adapter or backend override; no authenticated writes. Outside test/ to keep normal tests isolated. |
| `flutter test test/upload_progress_test.dart` | 1 passed | Slow upload, 0/50/100% feedback, disabled duplicate action, failure cleanup/retry |
| Dart format verification | 3 files, 0 changes, exit 0 after cache access allowed | Formatting only; first formatter successfully formatted files but exited 1 on sandbox telemetry write |
| `node scripts/database_test/verify_active_signup.mjs` | Passed | In-memory actual PostgreSQL, final full-UUID workspace fix, RLS/rollback; no hosted writes |
| `.venv\Scripts\python.exe scripts/database_test/verify_api_workflow.py` | 18 API + 50 SQL checks passed | Real FastAPI, real SQL/functions/model; controlled Auth/Storage |
| PDF capture rerun via `python -m tmp.audit_pdf_workflow` | Same 18 API + 50 SQL checks passed; exit 0; 2-page PDF, 376,947 bytes on rerun | Captures real workflow PDF and rasterizes pages locally; first PowerShell redirected run reported NativeCommandError from warnings despite completed checks, so rerun directly |
| `.venv\Scripts\python.exe -m pip check` | No broken requirements | Installed environment consistency; not a CVE scan |
| Actual backend startup | Passed; checkpoint warm-up and Uvicorn startup complete | Existing configured development environment |
| `python -m tmp.audit_readonly` | Localhost/Tailscale health 200/healthy; hosted settings/schema/buckets 200; anonymous patients 401 | Read-only actual services. Initial sandbox ConnectErrors resolved with network permission. |
| `python -m tmp.audit_local_api` | OpenAPI exact match; ten missing-token 401s; invalid-token 401 on retry | Actual HTTP and GoTrue rejection; first invalid-token assertion failed with provider timeout/503 |
| `flutter build apk --debug --dart-define=API_BASE_URL=http://100.99.7.24:8000/api/v1` | Baseline and post-fix builds passed (89.1 s / 25.3 s); final formatting refresh passed in 22.5 s | Actual Android debug compilation; not an install/device run |
| `adb devices -l` | No devices attached | Physical install, native integration_test and frame profiling not run |

Warnings include Starlette multipart/AnyIO deprecations, Pydantic model_ namespace
warnings, deprecated GoTrue/Supafunc packages and an unset root pytest-asyncio loop
scope warning at startup. They did not fail tests; dependencies were not upgraded
during this stability audit. Root pyproject.toml is the effective pytest config,
so the loop option in backend/pytest.ini is not used by root commands.

No live signup/login, recovery email/reset, patient write, Storage upload, authenticated
two-workspace test or phone integration test is included in the pass counts above.
Historical audit results were not added to current totals.

## Changed files and evidence

Application/test changes:

1. `frontend/flutter_app/lib/services/screening_service.dart`: optional Dio progress callback.
2. `frontend/flutter_app/lib/screens/screening/screening_screen.dart`: upload progress, waiting text, cleanup.
3. `frontend/flutter_app/test/upload_progress_test.dart`: slow/error/duplicate-action regression.

Documentation changes: this audit, a supersession note in `docs/CURRENT_PROJECT_STATUS.md`,
updated phone/testing guidance in `frontend/flutter_app/FRONTEND_GUIDE.md`, and appended
audit entries in `docs/agents/WORK_LOG.md` and `IMPLEMENTATION_PLAN.md`.

Temporary audit scripts/evidence (ignored under tmp): `audit_readonly.py`,
`audit_local_api.py`, `audit_artifacts.py`, `audit_pdf_workflow.py`, corresponding
JSON/log evidence, pytest temporary directories and `tmp/pdfs/audit-ai-*` artifacts.
The one-off real Flutter transport test is under `frontend/flutter_app/tmp/`.
Flutter regenerates build/cache metadata. No Git repository metadata was available
in this workspace, so a trustworthy git diff/clean-worktree claim is not possible.

## Final checklist

| Readiness item | Local evidence | Still required |
|---|---|---|
| Backend starts/model loads | Passed | Keep PC/backend awake during testing |
| Supabase connection | Live read passed | Stable Auth + DB + Storage workflow |
| Authentication | Controlled tests; live invalid/missing-token denial | Successful private credentials, new signup/login, native restore/logout |
| Patient management | Actual local SQL/API + widgets | Hosted create/search/select in correct workspace |
| Upload/QC | Validator/QC/API/widget tests | Native gallery/camera and hosted private object roundtrip |
| AI/five probabilities/Grad-CAM | Real checkpoint + actual local SQL persistence passed | Hosted save/reload and phone rendering |
| Screening saved correctly | Actual local SQL passed | Hosted persistence after restart |
| Technician AI PDF | Actual local SQL/model PDF passed without clinical report | Hosted PDF and native viewer |
| PDF open/download | Fixture/file handling tests passed | Phone viewer/save behavior |
| Workspace isolation | Actual local SQL/API and backend regressions passed | Two real hosted role tokens, Storage and PDF denial |
| Icon/splash | Assets and native resources checked | Visual phone launch/crop |
| Android debug build | Passed | Install and smoke on Android 7+ phone |
| Configurable physical API URL | Dart define + APK string + PC-side Tailscale health verified | Phone-side Tailscale reachability/ACL |
| Critical local errors | None reproduced after fix/retest | Close hosted/device acceptance gaps before claiming full E2E completion |

## Exact run/install commands

Use a normal PowerShell terminal. Root .env already contains backend configuration;
keep its values private and do not copy them into Flutter. From the project root:

```powershell
Set-Location C:\Users\HP\NETRAVA_1
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --no-access-log
```

The audit-started backend was verified on port 8000. If it is still running, use it
rather than starting a second process. Verify from the PC:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
Invoke-RestMethod http://100.99.7.24:8000/api/v1/health
```

Enable USB debugging, connect/unlock the phone and accept its RSA prompt. Ensure the
phone and PC are on the intended Tailscale network and permit the needed port via
their existing ACL/firewall configuration. Do not open the backend to the public
internet or make firewall/ACL changes automatically. Open this URL in the phone's
browser first: `http://100.99.7.24:8000/api/v1/health`.

```powershell
Set-Location C:\Users\HP\NETRAVA_1\frontend\flutter_app
flutter devices
flutter pub get
$phoneId = Read-Host 'Paste the Android device ID listed by flutter devices'
flutter run --debug -d $phoneId --dart-define=API_BASE_URL=http://100.99.7.24:8000/api/v1
```

To build/install the APK without Flutter hot reload:

```powershell
flutter build apk --debug --dart-define=API_BASE_URL=http://100.99.7.24:8000/api/v1
& 'C:\Users\HP\AppData\Local\Android\sdk\platform-tools\adb.exe' devices -l
& 'C:\Users\HP\AppData\Local\Android\sdk\platform-tools\adb.exe' -s $phoneId install -r .\build\app\outputs\flutter-apk\app-debug.apk
```

For a standard emulator, explicitly use `http://10.0.2.2:8000/api/v1` instead.
Release builds require HTTPS and production signing; the debug Tailscale command
above is the intended physical development-test configuration.

## Remaining manual acceptance steps

1. Confirm the phone health URL, icon and splash; install a PDF viewer if absent.
2. Use an existing authorized test account. Verify login, wrong password feedback,
   app restart/session restoration and logout. Do not share passwords/tokens in chat.
3. If signup acceptance is needed, deliberately register an approved test account
   and verify immediate login/private workspace. The agent did not create one here.
4. With explicit approval for hosted test writes, register a clearly synthetic
   patient; search/select it, test OD and OS, gallery and suitable fundus-camera capture.
   Test invalid, corrupt, oversized and poor-quality images without altering QC.
5. Analyze the exact uploaded bytes; inspect all probabilities/Grad-CAM, retain the
   screening/prediction IDs, verify saved rows/objects in that workspace and repeat
   lookup after restarting. Recent report cards themselves are session-only.
6. As technician, generate the AI PDF, view/download/open it and check both pages.
   Confirm no clinician-signed report is required and no clinical sign-off is granted.
7. With a separately authorized second workspace account, test patient, image,
   prediction, clinical report and AI PDF isolation. Test technician clinical-review
   rejection and clinician sign-off immutability without changing existing real data.
8. Review recovery redirect/template/SMTP configuration before requesting an email;
   owner completes the mailbox/reset/new-password acceptance. Do not reset existing
   passwords automatically.
9. Test small displays, larger text, back navigation, slow network, interrupted upload,
   missing viewer and low-memory camera return. Measure frame timings before changing
   working UI code. Avoid repeated writes after an ambiguous timeout.

The existing optional terminal procedure supports the technician path:

```powershell
Set-Location C:\Users\HP\NETRAVA_1
.\.venv\Scripts\python.exe scripts/verification/verify_live_backend.py --check-fixture
.\.venv\Scripts\python.exe scripts/verification/verify_live_backend.py --ai-report
```

The second command prompts privately and requires YES before retaining synthetic
hosted patient/screening/audit data. Run it only when those writes are explicitly
approved. It is not a substitute for native phone acceptance. Do not apply a schema
migration, alter RLS/permissions, confirm an existing account or change any live
record as an automatic response to a failed check.
