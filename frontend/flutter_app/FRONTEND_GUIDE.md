# NETRAVA Flutter integration

The active Android client uses the existing FastAPI API. Production code has no
mock login, prediction, quality check or generated clinical findings. Test fixtures
exist only under `test/`.

## Start

Run the backend from the repository root in a terminal with network access:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Run Flutter from `frontend/flutter_app`:

```powershell
flutter pub get
flutter run -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1
```

10.0.2.2 maps the standard Android emulator to its host computer. For the current
physical phone/Tailscale setup, use:

```powershell
flutter devices
$phoneId = Read-Host 'Android device ID'
flutter run --debug -d $phoneId --dart-define=API_BASE_URL=http://100.99.7.24:8000/api/v1
```

First check `http://100.99.7.24:8000/api/v1/health` in the phone browser with both
devices connected to the intended Tailscale network. See
`../../docs/FINAL_ANDROID_READINESS_AUDIT.md` for fresh results and acceptance steps.
Local HTTP is enabled only
in the Android debug manifest. Release configuration requires HTTPS:

```powershell
flutter build apk --release --dart-define=API_BASE_URL=https://your-backend.example.com/api/v1
```

The inherited Android release configuration still uses debug signing. Configure
production signing before distribution. Android is the verified target; iOS,
desktop and web have not been acceptance-tested. Native PDF handling uses dart:io.

## Implemented screens

- Branded startup/session recovery and real email/password login.
- Role-aware home with quick actions and session-only recent screening IDs.
- Searchable patient registry, pagination, registration and read-only details.
- Intake includes MRN, name, DOB, gender, phone, diabetes type/duration, HbA1c,
  insulin dependence and notes with backend-aligned limits.
- OD/OS image import/camera capture, real upload and quality assessment.
- Analysis loading state, grade/confidence/referral, five probabilities,
  original image and actual returned Grad-CAM overlay.
- Result-page AI PDF generation with current screening/prediction IDs, without clinician review.
- Technician Reports tab lists patient/date/grade/confidence for saved results from this session; reference lookup is also available.
- Separate clinician/admin drafts and immutable sign-off.
- Authenticated PDF download into private temporary app storage and external open.
- Trusted profile refresh and logout.

## Contracts and state

`core/config/api_config.dart` is the only API URL configuration. `core/network`
attaches bearer tokens, normalizes nested/top-level/binary errors and never logs
secrets. `models` parse responses; `services` implement endpoint contracts;
`providers/session.dart` manages authentication and dependency injection. Screens
own their loading/form state. ChangeNotifier is sufficient; no extra state package
is required. Shared cards/controls use the green design tokens and local Poppins.
Older prototype files are preserved outside the active navigation path.

JWTs use platform-backed secure storage. Restore verifies `/auth/me`. HTTP 401
clears memory and protected navigation. Logout removes stored authentication and
temporary report PDFs; external viewer copies are outside the app's control.
Android backup is disabled. There is no refresh-token API, so expired sessions
require login. Supabase keys and backend secrets must never be copied to Flutter.

Images remain in memory as original bytes. Upload feedback shows transferred bytes
as a percentage, then a separate server QC/save waiting state; 100% transfer does
not establish successful persistence. `/screenings` receives multipart
patient_id, eye and image. `/predict` receives retinal_image_id in the query and
the identical image bytes as multipart. Do not resize/re-encode between calls.
The app checks JPEG/PNG signatures and 15 MiB size. Server decode, pixel limit,
clinic authorization, QC and byte-hash checks remain authoritative.

Writes are not automatically retried. A timeout may occur after persistence;
check saved state before resubmitting. Returning from a successful result screen
reuses the existing prediction rather than repeating inference.

## Existing API limitations

Signup and Forgot Password are now implemented; see `../../docs/FINAL_ANDROID_READINESS_AUDIT.md` for current acceptance evidence. There is no OAuth, role selection, profile edit, patient edit/delete,
screening list, prediction history or clinician-queue endpoint. The AI Reports tab
uses actual saved result metadata from this signed-in session and pins each prediction.
Historical results can be opened by screening reference, using the latest saved prediction.
No fake counters/history or unsupported account controls are shown.

Each upload creates one screening and one eye. Signed image URLs expire in 30
minutes; no renewal route exists. Returned base64 Grad-CAM is preferred when
available. Reviews link to the latest prediction on the server. Only clinician
and administrator roles can write reviews. Draft reports may be downloaded;
signed reports are locked. AI PDFs use authenticated
`GET /screenings/{screening_id}/ai-report/pdf?prediction_id={prediction_id}`;
they embed private retinal/Grad-CAM images when available and never require a clinical report.
Missing optional images are labelled. Clinical `/report` routes remain separate.

## Verify

```powershell
flutter analyze
flutter test
flutter test integration_test/emulator_smoke_test.dart -d emulator-5554
flutter build apk --debug
```

Nineteen unit/widget tests exercise secure session restore/logout, exact multipart
bytes/query IDs, error envelopes, patient aliases, review/PDF contracts, technician
navigation through upload/QC/prediction/report, and clinician draft/sign-off. These
use isolated HTTP fixtures. The Pixel smoke test uses actual native secure storage
and actual backend health connectivity; it is not a live authenticated workflow test.

Runtime packages added: dio, flutter_secure_storage, image_picker, path_provider,
open_filex. Tests use integration_test and image_picker_platform_interface.
pubspec.lock records exact resolved versions. PDF opening requires an installed
viewer; downloaded bytes remain in private app temporary storage if none exists.

Windows Flutter desktop plugin generation can require symlink support. This
workspace uses local generated directory junctions in desktop ephemeral folders;
these are generated artifacts and do not change machine security settings.
