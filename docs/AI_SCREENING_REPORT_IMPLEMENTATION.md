# NETRAVA AI Screening Report implementation

Date: 2026-11-15

## Status

READY FOR END-TO-END TESTING. Not FULLY VERIFIED.

The AI report is independent of clinician review. Technicians can generate it without receiving administrator, ophthalmologist, review or sign-off privileges.

## Files changed

Backend:
- `backend/app/api/v1/screening.py`: authenticated AI report PDF route.
- `backend/app/services/report_service.py`: workspace-authorized persisted data retrieval and private image loading.
- `backend/app/services/report_pdf.py`: AI report variant, original image, Grad-CAM, full severity labels, required disclaimer and optional absent probabilities.
- `backend/requirements.txt`: PyMuPDF for PDF content and image verification tests.
- `backend/tests/test_ai_screening_report.py`: authorization, data mapping, relationship, assets and storage failure regressions.

Flutter:
- `frontend/flutter_app/lib/screens/results/result_screen.dart`: Generate Report action enabled only for a persisted prediction with an ID.
- `frontend/flutter_app/lib/screens/reports/ai_report_screen.dart`: generation progress, retry errors, View Report and Download/Open Report actions.
- `frontend/flutter_app/lib/services/report_service.dart`: authenticated binary AI PDF request.
- `frontend/flutter_app/lib/services/pdf_files.dart`: injectable directory/viewer dependencies for private-file verification; production defaults retained.
- `frontend/flutter_app/test/ai_report_test.dart`: generation, errors and loading state.
- `frontend/flutter_app/test/pdf_files_test.dart`: exact PDF bytes, viewer handoff, cleanup and invalid response rejection.
- `frontend/flutter_app/test/workflow_test.dart`: technician workflow now exercises the separate AI PDF.
- `frontend/flutter_app/test/support/fixture_api.dart`: AI PDF fixture and controllable response gate.

Documentation:
- `docs/AI_SCREENING_REPORT_IMPLEMENTATION.md`: this implementation and acceptance report.
- `docs/agents/WORK_LOG.md`: implementation and validation entry.

No database migration, bucket policy, credentials, model or application configuration was changed. Generated QA artifacts are under `tmp/pdfs/ai-screening-qa*`; the debug Android build is under `frontend/flutter_app/build/app/outputs/flutter-apk/app-debug.apk`.

## Architecture

Flutter result screen -> separate AI report screen -> authenticated GET `/api/v1/screenings/{screening_id}/ai-report/pdf` -> existing FastAPI JWT/profile dependency -> authorized Supabase database queries -> private Supabase Storage downloads -> ReportLab PDF bytes -> Flutter memory -> private app file -> device PDF viewer.

The backend first scopes the screening and patient to the trusted user's clinic/workspace. It selects the latest persisted prediction among images linked to that screening. Probabilities and explanations are fetched by that prediction ID. Only the selected prediction's original retinal image and Grad-CAM appear in the PDF. AI report identity is derived as `AI-{prediction_id}`; no clinician report row or sign-off is created. Repeated generation reconstructs the report from persisted data, with the current generation timestamp.

The PDF includes patient name/code/ID, recorded DOB/sex, screening timestamp/status/ID, eye side, prediction ID, grade and full severity name, confidence, stored class probabilities, original image and Grad-CAM when available, plus the requested disclaimer. Missing optional assets are explicitly identified. Absent probabilities are identified rather than invented; malformed stored distributions fail validation.

## Security

Existing JWT verification and active profile/workspace lookup are reused. No clinic ID is accepted from Flutter. Cross-workspace screenings return 404 before patient/image/prediction reads. The patient is independently workspace-scoped. Prediction/image and explanation/prediction relationships are constrained by database filters.

Private image paths must use the authenticated clinic prefix, fixed expected bucket and safe path components. Paths in another workspace fail closed. No arbitrary URL is fetched and no medical bucket is made public. Image decoding is bounded, JPEG/PNG checked and resized for embedding. Missing or unreadable optional objects produce an explicit unavailable message.

PDF responses use `application/pdf`, attachment disposition, `Cache-Control: no-store` and `nosniff`. Flutter checks the PDF signature and guards the download/open flow against a changed user. Local PDFs use the existing private temporary directory and existing logout/startup cleanup. An external PDF viewer receives medical data when the user chooses View/Open; this is device-dependent behavior.

Existing clinical report routes and clinician-only review/sign-off permissions remain in place; a technician still receives 403 when trying to submit a clinical review.

## Testing results

### Local / PDF layout

Generated a synthetic two-page AI report, extracted text and image placements, rendered both pages with PyMuPDF, and visually inspected the latest pages. No clipped content or overlapping tables/images was observed. QA images are synthetic placeholders, not patient records.

### Backend

Final full backend suite: 146 passed, including all 8 AI report tests. Existing clinical PDF/roundtrip tests also pass. Full backend checks include the existing real checkpoint/Grad-CAM tests; they are not a live Supabase acceptance run.

Checks cover saved-data mapping, patient name/code, grade, confidence, disclaimer, exact private bucket/path association, two embedded image placements, absent images/Grad-CAM/probabilities, storage download failure, unrelated predictions, cross-workspace patient/screening, inconsistent image path, missing/invalid bearer authentication, technician PDF access and preserved clinician-only write authorization.

### Flutter

Final full Flutter suite: 16 passed, including the dedicated progress test. Analyzer: no issues. Debug Android APK built successfully. Fixture tests exercise technician login, patient selection, upload/QC, AI result, saved prediction and AI PDF generation; clinician draft/sign-off tests continue to pass. Private file tests verify exact saved bytes, viewer callback invocation, invalid PDF rejection and cleanup. These use fixtures and a viewer callback, not a real Android PDF viewer.

### Real end-to-end live testing

NOT EXECUTED in this session. No authenticated real test-user session was supplied. No real patient/screening was created in hosted Supabase by this change, and no Android device PDF-viewer acceptance was performed. Existing project evidence is not substituted for a fresh acceptance run.

## Remaining acceptance steps

1. Run the updated backend and Android app against the intended private Supabase workspace.
2. Log in or sign up as a real technician; register a clearly marked test patient.
3. Select that patient, upload a gradable retinal image, run QC and real AI/Grad-CAM, and confirm the prediction is saved.
4. Choose Generate Report, then generate the AI PDF. Compare patient identifiers, eye, screening/prediction IDs, grade, confidence and probability values with the saved database/result.
5. Choose View Report and Download/Open Report on the Android device. Confirm the original image and Grad-CAM are correct, the disclaimer appears and logout clears app-private report files. A device PDF viewer must be installed.
6. Repeat the PDF request with no/invalid authentication and with a real account from another workspace; confirm rejection.
7. Verify a saved screening with unavailable optional assets still generates a clearly labelled report.

Only after this real Flutter -> backend -> AI -> Supabase -> PDF -> Flutter/device flow succeeds should status become FULLY VERIFIED. The feature presently supports private app saving and external opening; it does not export to public Downloads or provide an embedded PDF viewer.
