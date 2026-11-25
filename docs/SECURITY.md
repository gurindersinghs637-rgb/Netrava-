# NETRAVA — Security, Privacy & Medical Compliance Architecture

**Document Version:** 1.0.0  
**Authority:** Senior Software Architect & Lead Security Auditor  
**Standard Compliance:** HIPAA Privacy Rule, GDPR Healthcare Safeguards

> This document describes security requirements and design goals. It is not a certification or evidence of regulatory compliance. Current implementation and verification limits are recorded below.

---

## 1. Healthcare Security Philosophy

Retinal fundus imagery and diabetic patient records represent sensitive Protected Health Information (PHI) and Personally Identifiable Information (PII). A breach could result in identity theft, unauthorized medical profiling, and severe regulatory penalties.

NETRAVA adheres to a **Zero-Trust Defense-in-Depth** model:
1. **Never Trust Client Payloads:** All inputs are strictly validated at the API boundary.
2. **Never Expose Direct Storage URLs:** Images are accessible only via ephemeral, cryptographically signed URLs.
3. **Never Allow Unrestricted Database Access:** Multi-tenant isolation is enforced in the database kernel via PostgreSQL Row Level Security (RLS).
4. **Audit Every Diagnostic Event:** Clinical assessments, overrides, and report signatures generate immutable audit logs.

---

## 2. Authentication & Authorization (RBAC)

- **Identity Management:** Managed via Supabase GoTrue issuing cryptographically signed RS256/HS256 JSON Web Tokens (JWT).
- **Session Tokens:** Short-lived access tokens (1-hour expiration) paired with secure HTTP-only refresh tokens.
- **Role Verification:**
  - `technician`: Restricted to screening operations in their registered clinic.
  - `ophthalmologist`: Clinical review authority; permitted to view all cases in their medical network and sign reports.
  - `administrator`: Operational controls, account provisioning, audit log inspection.
- **Service Role Key Security:** The Supabase `service_role` secret key is **never** shipped in the Flutter client binary or exposed via public APIs. It resides exclusively in backend server environment variables.

---

## 3. Storage Security & Media Access Control

- **Private Storage Buckets:** All buckets (`fundus-images`, `gradcam-heatmaps`, `clinical-reports`) are configured with `public = false`.
- **Signed URL Policy:**
  - Client devices never receive permanent object storage URLs.
  - When an authorized technician or ophthalmologist views a scan or heatmap, the backend generates an HMAC-signed URL valid for a maximum of 30 minutes.
  - Replay attacks are mitigated through short expirations and token single-use constraints.

---

## 4. Input & File Upload Validation

To prevent Remote Code Execution (RCE) and buffer overflow vulnerabilities:
- **Header Magic Bytes Check:** Beyond checking file extensions (`.jpg`, `.png`), the backend inspects the initial file bytes to verify genuine image headers (`\xFF\xD8\xFF` for JPEG; `\x89PNG\r\n\x1a\n` for PNG).
- **File Size Caps:** Uploads are strictly capped at 15 MB. Larger payloads are rejected with `413 Payload Too Large`.
- **Image Decompression Bomb Defense:** Pillow decompression bomb protection is enabled (`Image.MAX_IMAGE_PIXELS = 50_000_000`) to prevent denial-of-service memory exhaustion.

---

## 5. Audit Logging & Compliance Ledger

The `audit_logs` table maintains an immutable record of:
- Every AI prediction generated (model version, inference latency, prediction grade).
- Every ophthalmologist override of an AI severity classification (previous grade, new grade, clinical rationale).
- Every report digitally signed or exported.
- Every login attempt, IP address, and client user-agent.

## 6. Current implementation and verification status

- Non-test API requests validate the access token by calling Supabase Auth, then load role, active status, and clinic membership from `user_profiles`. Local HS256 tokens are accepted only with `ENVIRONMENT=testing`.
- Patient, screening, prediction, report, and storage operations are scoped using the trusted profile's clinic ID. The service-role key is not part of the Flutter app or API responses.
- The initial SQL migration adds clinic-level RLS, private buckets with no direct authenticated storage policies, transaction RPCs, and append-only audit records. The backend uses the service role and returns short-lived signed URLs for media reads. The migration has not been executed against any database; its policies and RPCs are not yet verified by PostgreSQL.
- The current audit RPCs record patient creation, screening creation, prediction creation, and ophthalmologist review. Login-attempt logging, report PDF export, retention rules, and audit-log viewing endpoints are not implemented.
- Supabase credentials are not configured in this workspace. Local tests mock data services or verify fail-closed behavior; no live JWT, RLS, storage, or database operation has been performed.
- No HIPAA/GDPR compliance certification, clinical validation, penetration test, or production security assessment has been performed.



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
