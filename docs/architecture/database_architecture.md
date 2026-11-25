# NETRAVA — Deep-Dive Database Architecture

**Component:** PostgreSQL & Supabase Cloud Infrastructure  
**Document Version:** 1.0.0  
**Authority:** Agent 05 (Database Engineer)

---

## 1. Storage Optimization & Indexing Strategy

To guarantee rapid clinical triage queries in clinics with tens of thousands of historical scans:
1. **B-Tree Indexes:** Placed on foreign keys (`patient_id`, `screening_id`, `retinal_image_id`, `technician_id`).
2. **Descending Timestamp Indexes:** `idx_screenings_created ON public.screenings(created_at DESC)` enables instant dashboard queue loading without sequential table scans.
3. **Full-Text Search Index:** `idx_patients_name ON public.patients USING gin (to_tsvector('english', full_name))` provides sub-10ms search by patient name.
4. **Alphanumeric Unique Index:** `idx_patients_mrn ON public.patients(mrn)` ensures instantaneous lookup by Medical Record Number.

---

## 2. Temporal & Audit Integrity

- **Automatic Timestamp Updates:** Trigger functions automatically update `updated_at` timestamps on row modifications.
- **Cascading Integrity:** Deleting a screening cascade-deletes associated images, predictions, and explanations, preventing orphaned media in storage.
- **Immutable Audit Logging:** The `audit_logs` table has permissions restricted so that even authenticated users cannot update or delete existing audit entries (`INSERT` and `SELECT` only).

