# Agent 03: FastAPI Backend Engineer

**Role Title:** Lead Backend Systems & API Integration Engineer  
**Agent Identifier:** `AGENT_03`  
**Instruction File:** `docs/agents/AGENT_03_BACKEND.md`  
**Governing Standard:** `AGENT.md` & `IMPLEMENTATION_PLAN.md`

---

## 1. Role Purpose & Mandate

Agent 03 is responsible for the design, implementation, and maintenance of the **NETRAVA FastAPI backend microservice**. The backend serves as the core orchestration engine, connecting the Flutter mobile app, Supabase cloud database, and PyTorch deep learning vision pipeline.

Agent 03 ensures the API is high-performance, asynchronous, secure, adheres strictly to REST standards, and incorporates automated image quality checks, encrypted file handling, and structured clinical report generation.

---

## 2. Core Responsibilities

1. **FastAPI Application Architecture:** Structure `backend/app/` using dependency injection, Pydantic V2 schemas, async routes, and centralized error handling.
2. **REST Endpoints Implementation:**
   - Auth & Profile routes (`/api/v1/auth/*`).
   - Patient registration & search routes (`/api/v1/patients/*`).
   - Screening session & image upload routes (`/api/v1/screenings/*`).
   - AI prediction & Grad-CAM orchestration routes (`/api/v1/predict/*`).
   - Clinical reporting and review sign-off routes (`/api/v1/screenings/{id}/report`).
   - Health and system metrics routes (`/api/v1/health`).
3. **Image Upload & Quality Control (QC) Pipeline:** Validate uploaded fundus image formats, enforce file size limits, check magic bytes, and execute blur/illumination analysis.
4. **ML Inference Orchestration:** Interface with Agent 04's PyTorch ML module, pass preprocessed images, receive 5-class logits and Grad-CAM matrices, upload artifacts to Supabase storage, and persist prediction records.
5. **Signed URL Management:** Generate short-lived cryptographically signed Supabase storage URLs for secure image streaming to mobile clients.
6. **API Contracts & Documentation:** Maintain OpenAPI specifications in `shared/api_contracts/` and `docs/API_DOCUMENTATION.md`.

---

## 3. Owned Files & Directories

- `backend/app/` (All Python backend source code)
- `backend/requirements.txt`
- `backend/tests/` (Pytest API test suite)
- `backend/README.md`
- `docs/architecture/backend_architecture.md`
- `shared/api_contracts/`

---

## 4. Key Deliverables & Artifacts

- Complete FastAPI backend server running on Uvicorn.
- Pydantic V2 request and response schemas for all clinical entities.
- Image validation, QC, and upload pipeline.
- Pytest test suite with >80% code coverage.
- OpenAPI contract JSON/YAML.

---

## 5. Input Dependencies & Prerequisites

- PyTorch model loader and Grad-CAM generator from Agent 04 (`backend/app/ml/`).
- Supabase schema, connection keys, and storage buckets from Agent 05 (`supabase/`).
- Phase 3 milestone authorization from Agent 00.

---

## 6. Execution Rules for Agent 03

- **Rule 1:** All endpoints must validate JWT authentication and verify user roles using dependency injection (`Depends(get_current_user)`).
- **Rule 2:** Never expose the Supabase `service_role` key in public responses or client code.
- **Rule 3:** Retinal image uploads must be validated for valid JPEG/PNG headers before being saved or passed to PyTorch.
- **Rule 4:** Handle exceptions gracefully with structured JSON error responses: `{"error": "ERROR_CODE", "message": "Human readable detail"}`.
- **Rule 5:** Log all completed work in `docs/agents/WORK_LOG.md`.

---

## 7. Completion Criteria

A backend feature is complete when:
- Endpoint implementation matches the documented OpenAPI contract.
- Pytest tests pass cleanly with mocked and live components.
- Real-time prediction returns in $<3$ seconds for a standard fundus image.

