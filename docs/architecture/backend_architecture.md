# NETRAVA — Deep-Dive Backend Architecture

**Component:** FastAPI REST Microservice  
**Document Version:** 1.0.0  
**Authority:** Agent 03 (Backend Engineer)

## Current implementation note (2026-11-03)

The current application uses FastAPI routers, service modules, the Supabase Python client for PostgREST/storage/RPC calls, and HTTPX for Supabase Auth verification. It does not currently contain the SQLAlchemy ORM models or async database-session provider pictured as future architecture below. Supabase access is unverified until a development project is configured and the local migration is applied there.

---

## 1. Application Layering & Design Patterns

The backend follows the **Repository-Service-Controller (RSC)** pattern:

```
FastAPI Router (app/api/v1/)
       │
       ▼
Service Layer (app/services/)  <──> ML Pipeline (app/ml/)
       │
       ▼
Data Layer (SQLAlchemy ORM + Supabase SDK)
       │
       ▼
PostgreSQL Database + Private S3 Storage
```

1. **Routers (`app/api/v1/`):** Thin HTTP entry points handling route definitions, status codes, query parsing, and response serialization using Pydantic V2 models.
2. **Services (`app/services/`):** Encapsulate all business logic:
   - `patient_service.py`: Intake validation, duplicate MRN detection, diabetes risk scoring.
   - `screening_service.py`: Image QC assessment, multipart dispatch, session tracking.
   - `prediction_service.py`: Orchestrates PyTorch inference, computes Grad-CAM, and saves prediction metadata.
   - `report_service.py`: Formats clinical summaries and generates downloadable PDF reports.
3. **ML Module (`app/ml/`):** Pure machine learning logic decoupled from web frameworks:
   - `model_loader.py`: Singleton model manager.
   - `preprocessing.py`: Image transforms.
   - `prediction.py`: Class probability extraction.
   - `gradcam.py`: PyTorch hook manager.
   - `qc.py`: Laplacian blur filter.
4. **Data Access (`app/database/`):** Asynchronous database sessions and Supabase API clients.

---

## 2. Thread Safety & Model Concurrency

In PyTorch, model forward passes are thread-safe in `eval()` mode. However, Grad-CAM requires backpropagation (`logits.backward()`) which modifies tensor gradients.

To guarantee concurrency safety during simultaneous screening requests:
- Each prediction request executes within a Python thread lock (`asyncio.Lock()` or `threading.Lock()`), or operates on a localized forward/backward hook context.
- Hooks are strictly cleaned up in `finally:` blocks:
  ```python
  forward_handle.remove()
  backward_handle.remove()
  ```
- Memory is immediately reclaimed using `torch.cuda.empty_cache()` if running on GPU.



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


Public signup (2026-11-14): POST /api/v1/auth/signup accepts full_name, email, password, confirm_password only. Returns 201 pending_approval. Requires the Auth profile trigger migration; assigns inactive technician with no clinic. See docs/AUTH_SIGNUP_REPORT.md for deployment, errors and approval lifecycle.


2026-11-14 simplified signup supersedes pending approval: /api/v1/auth/signup now requires phone, creates an active technician in a separate private workspace via migration 202611140002_active_signup.sql, and returns active or email_confirmation_required. No administrator approval. Existing JWT/clinic isolation remains. See docs/AUTH_SIGNUP_REPORT.md.


Password recovery: POST /api/v1/auth/forgot-password {email}; POST /api/v1/auth/reset-password {token_hash,password,confirm_password}. GET /api/v1/auth/reset-password serves the browser form. Configurable PASSWORD_RESET_REDIRECT_URL and Supabase recovery template required. See docs/PASSWORD_RECOVERY_REPORT.md.
