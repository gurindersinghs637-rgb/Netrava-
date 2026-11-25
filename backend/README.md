# NETRAVA FastAPI backend

This backend is the existing API and inference service. Work in this folder continues the established project; it is not a project rebuild.

## Start locally

From the repository root, use the project Python 3.11 virtual environment:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

The model checkpoint path is resolved from the repository root. Run the command from the root so `backend.app` and `ai_model` imports resolve. API docs are at `http://127.0.0.1:8000/api/v1/docs`.

## Configuration

Copy the variable names from `.env.example` into a root `.env` file. Do not commit `.env`. Real Supabase login, protected routes, patient operations, screening storage, prediction persistence, reports, and audit logging require:

- `SUPABASE_URL`
- `SUPABASE_KEY` (public/anon key)
- `SUPABASE_SERVICE_ROLE_KEY` (backend only)

Apply the reviewed local migration to a development Supabase project before expecting persistence. The example values are placeholders; no project credentials are included. Production configuration also requires a unique `SECRET_KEY` of at least 32 characters.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests ai_model/tests -q
```

Tests use test-only local JWTs and mocks. They do not contact a live Supabase project. See `docs/PROJECT_HANDOFF.md` for current server and test verification.


## Current deployment and verification

See `docs/FINAL_BACKEND_READINESS_REPORT.md` for the authoritative current status.
The normalized migration in `supabase/migrations/202611130001_normalized_backend.sql`
is implemented and locally executed; the old conflicting migration is preserved
under `supabase/legacy/` and must not be applied.

Install runtime/test dependencies before starting:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

The supported additional route is authenticated
`GET /api/v1/screenings/{screening_id}/report/pdf`. It renders persisted clinical
fields and AI probabilities directly as a private PDF response. Review endpoints
preserve urgency, confirmed grade, override and notes. Prediction requests must
reuse the original screening image bytes.

Technician AI reports use authenticated
`GET /api/v1/screenings/{screening_id}/ai-report/pdf?prediction_id={prediction_id}`.
This returns PDF bytes directly without creating or requiring a clinician review.
The screening must belong to the JWT user's clinic, and the prediction must belong
to an image in that screening. Flutter's result action pins the current prediction;
opening from the Reports tab by screening ID uses the latest saved prediction.
The clinical `/report` and `/report/pdf` routes remain separate for clinical review.

Local actual-database workflow: `.\.venv\Scripts\python.exe scripts/database_test/verify_api_workflow.py`
(after `npm.cmd ci --prefix scripts/database_test`). Live operator verification:
`.\.venv\Scripts\python.exe scripts/verification/verify_live_backend.py`.
Do not start Flutter integration until deployed migration and live verification pass.
