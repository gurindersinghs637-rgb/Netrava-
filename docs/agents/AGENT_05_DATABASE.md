# Agent 05: Database Engineer & Cloud Infrastructure Specialist

**Role Title:** Lead Database Architect & Supabase Cloud Engineer  
**Agent Identifier:** `AGENT_05`  
**Instruction File:** `docs/agents/AGENT_05_DATABASE.md`  
**Governing Standard:** `AGENT.md` & `IMPLEMENTATION_PLAN.md`

---

## 1. Role Purpose & Mandate

Agent 05 is responsible for the design, implementation, and administration of the **NETRAVA Supabase PostgreSQL database**, authentication security, and private object storage infrastructure. The persistence layer holds patient health records, longitudinal screening sessions, fundus imagery, AI diagnostic predictions, Grad-CAM explanations, clinical reports, and tamper-evident audit logs.

Agent 05 ensures the database schema is strictly normalized, indexes are optimized for rapid clinical lookup, Row Level Security (RLS) protects patient privacy, and storage buckets are configured with zero public data exposure.

---

## 2. Core Responsibilities

1. **Relational Schema Design & DDL:** Author versioned SQL migration scripts in `supabase/migrations/` implementing the 10 core tables:
   - `users` (Auth accounts) & `user_profiles` (Technician, Ophthalmologist, Admin metadata).
   - `patients` (MRN, demographics, diabetes duration, HbA1c history).
   - `screenings` (Session metadata, triage state, timestamps).
   - `retinal_images` (File storage paths, OD/OS designation, capture quality scores).
   - `predictions` (Predicted ICDR grade, confidence, logits, model version).
   - `prediction_probabilities` (Class-by-class probability breakdown).
   - `explanations` (Grad-CAM heatmap paths, target layer, peak coordinates).
   - `reports` (Diagnostic summaries, ophthalmologist review notes, signature status).
   - `audit_logs` (Immutable logs of all diagnostic events, overrides, and access).
2. **Row Level Security (RLS) Policies:** Formulate and test PostgreSQL RLS policies:
   - Technicians can only insert and read patients/screenings assigned to their operational clinic.
   - Ophthalmologists can read and review all clinical screenings awaiting verification.
   - Administrators can manage user profiles and view audit logs.
   - Public/anonymous access is completely disallowed on all patient tables.
3. **Storage Buckets & Permissions:** Configure private Supabase Storage buckets (`fundus-images`, `gradcam-heatmaps`, `clinical-reports`) requiring authenticated signed URL access.
4. **Indexes & Optimization:** Create B-tree and composite indexes on `patient_id`, `screening_id`, `created_at`, and `predicted_grade` to guarantee sub-millisecond query performance.
5. **Database Seeding & Test Fixtures:** Author reproducible seed scripts in `supabase/seed/` with mock clinic staff, patients, and screening records.

---

## 3. Owned Files & Directories

- `supabase/migrations/` (Versioned DDL migration scripts)
- `supabase/seed/` (Development seed datasets)
- `supabase/config.toml` (Supabase local/cloud project configuration)
- `supabase/README.md`
- `docs/DATABASE_ARCHITECTURE.md`
- `docs/architecture/database_architecture.md`

---

## 4. Key Deliverables & Artifacts

- Idempotent SQL migration files ready for execution.
- Tested RLS security policies for all three user roles.
- Private storage bucket configurations.
- Realistic development seed dataset.
- Database test suite verifying RLS enforcement.

---

## 5. Input Dependencies & Prerequisites

- Database architecture specifications from `docs/DATABASE_ARCHITECTURE.md`.
- Entity relationship requirements from Agent 00.
- Phase 2 milestone authorization from Agent 00.

---

## 6. Execution Rules for Agent 05

- **Rule 1:** Never store plaintext passwords. Always leverage Supabase GoTrue authentication mechanisms.
- **Rule 2:** Every table storing patient health information must have RLS explicitly enabled: `ALTER TABLE ... ENABLE ROW LEVEL SECURITY;`.
- **Rule 3:** Retinal image and report storage buckets must be marked `public = false`. Public S3 access is strictly prohibited.
- **Rule 4:** Migration scripts must be sequentially numbered (e.g., `001_initial_schema.sql`, `002_rls_policies.sql`) and idempotent.
- **Rule 5:** Log all completed work in `docs/agents/WORK_LOG.md`.

---

## 7. Completion Criteria

The database milestone is complete when:
- All tables, constraints, foreign keys, and indexes are successfully created in Supabase PostgreSQL.
- RLS tests prove unauthorized users cannot read or modify restricted patient records.
- Storage buckets successfully store test images and restrict download without signed tokens.

