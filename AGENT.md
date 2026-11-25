# NETRAVA — Master AI Agent Instructions & Operating Manual

**File:** `AGENT.md`  
**Classification:** Core Project Operating Procedure (Mandatory Reading for All Agents)  
**Version:** 1.0.0  
**Authority:** Senior Software Architect & Lead Multi-Agent Coordinator

---

> [!IMPORTANT]
> **MANDATORY RULE FOR ALL AI CODING AGENTS:**  
> Before generating code, executing commands, or editing files in the NETRAVA repository, you **MUST** read this file and your assigned agent specification file in `docs/agents/AGENT_XX_*.md`.  
> Do not assume another agent has completed work simply because a file exists. **Inspect, verify, and test** the actual code before building on top of it.

---

## 1. What NETRAVA Is

**NETRAVA** (*"See. Detect. Explain."*) is an enterprise clinical healthtech system for point-of-care **Diabetic Retinopathy (DR)** screening. It combines deep convolutional neural networks with **Grad-CAM** visual explainability to detect microvascular lesions in retinal fundus images and grade severity across the 5-stage International Clinical Diabetic Retinopathy (ICDR) scale.

The platform coordinates three key healthcare roles:
1. **Field Technician:** Rapid patient intake, fundus camera alignment, real-time image quality control (QC), and preliminary AI screening.
2. **Ophthalmologist:** Diagnostic review, Grad-CAM lesion inspection, clinical grade verification/override, and tele-referral dispatch.
3. **Administrator:** Clinic operations, technician/clinician account provisioning, security governance, and audit log analysis.

---

## 2. Current Project Development Status

**Current audit (2026-11-15):** See `docs/CURRENT_PROJECT_STATUS.md`. Flutter and auth integration now exist following later owner requests; older backend-only notes below are historical. Fresh checks: 158 backend/AI tests, 11 Flutter tests and 16 API/50 SQL checks pass. Core live signup/login/profile evidence exists; fresh private technician clinical workflow, report handoff and real password recovery remain acceptance gates.


**Latest continuation (2026-11-13):** See `docs/FINAL_BACKEND_READINESS_REPORT.md`.
114 pytest tests, 50 actual PostgreSQL checks and 16 actual-SQL/real-model API
workflow checks pass; combined backend coverage is 85%. The compatible normalized
migration is implemented in `supabase/migrations/202611130001_normalized_backend.sql`.
The conflicting old migration is preserved under `supabase/legacy/`. Hosted
migration deployment and real-account/Storage verification are the remaining gate;
no live changes were made. Earlier notes below are historical. Flutter stays paused.


- **Current focus:** Backend-only continuation in NETRAVA_1. Do not start actual Flutter application development until all three backend phases have been completed and verified, then wait for the owner's approval.
- **Existing work:** EfficientNet-B3 checkpoint and inference package; FastAPI routes/services; a Flutter welcome/login prototype and design references. The prototype does not mean frontend development has started.
- **Backend status:** The latest complete local backend + AI suite passed **87 tests** (2026-11-03), including real-checkpoint inference/Grad-CAM, report PDF generation with synthetic data, and clinic-scoped patient/prediction query regressions. Local Uvicorn startup, docs/OpenAPI, and unauthenticated-route rejection were verified. Current health was `degraded`: model loaded, but this session's read-only Supabase request failed with a network `ConnectError`. Live user/JWT authentication, RLS, Storage object operations, and persistence remain unverified. Backend is not ready for Flutter integration.
- **Phase 3 blocker:** Root `.env` is configured; never print its values. Earlier read-only checks documented the existing table/bucket metadata, while the latest session could not reach Supabase from its network. Existing normalized probability/explanation tables differ from the local migration; report and write-function semantics are unresolved. Obtain a schema-only export (policies, constraints, indexes, function bodies/grants), review `rls_auto_enable`, and reconcile locally. Do not apply the current migration or change live policies/buckets without owner approval.
- **Current handoff:** `docs/PROJECT_HANDOFF.md` records the exact current test results, server health, prior live schema observations, blockers, and the next task.

---

## 3. Existing Trained Model Information

The AI model training phase is **complete**. Agents must adhere strictly to the following parameters:

- **Architecture:** EfficientNet-B3 (`timm.create_model('efficientnet_b3', pretrained=False, num_classes=5, drop_rate=0.30)`).
- **Trained Checkpoint Name:** `best_efficientnet_b3_staged.pth` (selected via highest Validation Quadratic Weighted Kappa).
- **Input Dimensions:** $300 \times 300$ pixels.
- **Aspect-Ratio Resizing:** Retinal fundus images are resized using `PIL.Image.Resampling.LANCZOS` preserving aspect ratio, zero-padded with black `(0, 0, 0)` borders to form a square $300 \times 300$ canvas (`ResizeWithPadding`).
- **Normalization:** Standard ImageNet Mean $[0.485, 0.456, 0.406]$ and Std $[0.229, 0.224, 0.225]$.
- **Target Layer for Grad-CAM:** `model.conv_head` (feature map extraction via forward hook; gradients captured via full backward hook).
- **Class Labels & Ordering:**

| Grade ID | ICDR Severity Grade | Clinical Description |
|---|---|---|
| **0** | No DR | Normal fundus; no microaneurysms or hemorrhages. |
| **1** | Mild NPDR | Microaneurysms only. |
| **2** | Moderate NPDR | Microaneurysms, dot/blot hemorrhages, venous beading. |
| **3** | Severe NPDR | Severe intraretinal hemorrhages (4 quadrants) or venous beading. |
| **4** | Proliferative DR (PDR) | Neovascularization, vitreous/preretinal hemorrhage. |

> [!CAUTION]
> **NEVER RETRAIN, OVERWRITE, OR ALTER THE TRAINED MODEL ARCHITECTURE.**  
> Any changes to normalization values, input resolution, layer names, or class ordering will invalidate the model checkpoint and break clinical accuracy.

---

## 4. Technology Stack

- **Mobile Client:** Flutter 3.x, Dart ^3.12, Material 3, Custom Painters, Dio HTTP, Provider/Riverpod.
- **Backend API:** Python 3.11+, FastAPI, Uvicorn, Pydantic V2, SQLAlchemy.
- **Deep Learning & CV:** PyTorch 2.2+, timm 0.9+, Pillow 10+, OpenCV (headless), NumPy.
- **Database & Cloud:** Supabase PostgreSQL 15+, GoTrue Auth, Row Level Security (RLS), Supabase Storage.
- **Reporting:** ReportLab / WeasyPrint (PDF generation).
- **Containerization:** Docker, Docker Compose.

---

## 5. Folder Structure

All work must strictly reside within the established project hierarchy:

```
NETRAVA/
├── README.md                          # Master project documentation
├── AGENT.md                           # Master instructions for all agents
├── IMPLEMENTATION_PLAN.md             # Phased roadmap with task gates
├── .gitignore                         # Git exclusion rules
├── .env.example                       # Environment template
├── docs/                              # Architecture, security, deployment docs
│   ├── agents/                        # Agent guidebooks and WORK_LOG.md
│   ├── architecture/                  # Deep-dive architecture specs & diagrams
│   └── references/                    # Medical papers and grading criteria
├── design_reference/                  # Single source of truth for UI/UX
│   ├── design_system/                 # COLORS.md, TYPOGRAPHY.md, SPACING.md, etc.
│   ├── branding/                      # Logos, icons, vector painters
│   └── screenshots/                   # 14 Reference screens with code & mockups
├── frontend/flutter_app/              # Flutter mobile client
├── backend/app/                       # FastAPI server and ML services
├── supabase/                          # Database migrations, seed scripts, RLS
├── ai_model/                          # Model checkpoint, research notebooks
├── shared/                            # OpenAPI contracts, shared constants
└── scripts/                           # Setup and deployment automation
```

---

## 6. Overall Architecture

NETRAVA is organized as a decoupled, event-aware, client-server system:
1. **Presentation Layer:** Flutter cross-platform client communicating via JSON/multipart REST over TLS.
2. **Gateway & Logic Layer:** FastAPI server performing token verification, payload validation, image quality checks, and service orchestration.
3. **Inference Layer:** PyTorch pipeline running EfficientNet-B3 forward inference and Grad-CAM backpropagation on GPU/CPU.
4. **Data & Storage Layer:** Supabase PostgreSQL storing relational entities; Supabase Storage holding raw fundus photos, Grad-CAM heatmaps, and signed reports in private buckets.

---

## 7. Database Architecture

The broader target persistence model includes Supabase Auth users and application tables for clinics, profiles, patients, screenings, retinal images, predictions, reports, and audit logs. The supported normalized migration is the executable schema definition; probabilities are rows in `prediction_probabilities` and Grad-CAM paths are in `explanations`. The old JSONB-based migration is archived under `supabase/legacy/`. Do not assume design-only entities or live policies exist until the migration has been applied and verified.

**Strict Security Rule:** Direct client access to medical images is prohibited. Access is restricted to temporary cryptographically signed URLs generated by the backend.

---

## 8. Design Reference Location

The single source of truth for UI/UX is the `design_reference/` directory:
- Design Tokens: `design_reference/design_system/` (`COLORS.md`, `TYPOGRAPHY.md`, etc.).
- Screen Prototypes: `design_reference/screenshots/` containing 14 subfolders, each equipped with `screen.png` visual mockup and `code.html` layout structure.
- Never invent arbitrary colors, font sizes, or screen layouts without consulting these reference materials.

---

## 9. Development Phases

The project uses the 8 structured phases detailed in `IMPLEMENTATION_PLAN.md`:
- Phase 0: Project Foundation (historical milestone completed)
- Phase 1: AI Model Integration
- Phase 2: Supabase Database & Auth
- Phase 3: FastAPI Backend Implementation
- Phase 4: Flutter Mobile Implementation
- Phase 5: Full System Integration
- Phase 6: Testing & Clinical Validation
- Phase 7: Production Deployment & Release

**Current owner gate:** Phases 2-3 (Supabase and backend) remain blocked on development-database verification. Phase 4 (Flutter) is not authorized to start until the owner approves after backend completion.

---

## 10. Agent Responsibilities

| Agent ID | Title | Primary Responsibility | Owned Directories |
|---|---|---|---|
| **Agent 00** | Project Coordinator | Roadmap, dependency gates, handovers | Root docs, `docs/` |
| **Agent 01** | Frontend Architect | Flutter client, state, navigation, API | `frontend/flutter_app/lib/` |
| **Agent 02** | UI/UX Designer | Design system fidelity, custom widgets | `design_reference/`, Flutter widgets |
| **Agent 03** | Backend Engineer | FastAPI server, API routes, security | `backend/app/` |
| **Agent 04** | AI/ML Integration Engineer | PyTorch inference, Grad-CAM, QC | `backend/app/ml/`, `ai_model/` |
| **Agent 05** | Database Engineer | Supabase DDL, RLS, storage buckets | `supabase/` |
| **Agent 06** | Testing & QA Engineer | Unit, integration, security test suites | `backend/tests/`, Flutter tests |
| **Agent 07** | Documentation Engineer | Technical docs, API specs, runbooks | `docs/`, `shared/` |

---

## 11. Coding Conventions

- **Python (Backend & ML):**
  - Follow PEP 8 style guide.
  - Type annotations are mandatory for all function parameters and return values.
  - Use Pydantic V2 models for all request/response serialization.
  - Asynchronous handlers (`async def`) for I/O and database operations.
  - Logging via standard Python logging or Loguru (never use bare `print()`).
- **Dart (Flutter):**
  - Adhere to effective Dart style rules.
  - Enforce `const` constructors wherever possible to optimize widget rebuilds.
  - Meaningful widget decomposition: keep individual build methods under 100 lines.
  - Colors and typography must reference `AppColors` and `AppTextStyles` tokens exclusively.
- **SQL (Supabase):**
  - Lowercase table and column names using snake_case (e.g., `retinal_images`).
  - Every table must have `id UUID PRIMARY KEY DEFAULT gen_random_uuid()` and `created_at TIMESTAMPTZ DEFAULT now()`.
  - Every table storing patient-identifiable data must have RLS enabled (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY;`).

---

## 12. File Ownership Rules

To prevent merge collisions and broken dependencies:
- Only **Agent 01** may modify `frontend/flutter_app/lib/`.
- Only **Agent 03** may modify `backend/app/api/` and `backend/app/services/`.
- Only **Agent 04** may modify `backend/app/ml/` and `ai_model/`.
- Only **Agent 05** may modify `supabase/migrations/` and `supabase/seed/`.
- Only **Agent 00** and **Agent 07** may modify root documentation and roadmap files.
- If an agent requires changes outside their owned domain, they must request the change via a Handover Note in `docs/agents/WORK_LOG.md`.

---

## 13. Git Collaboration Rules

- Never commit directly to the `main` branch.
- Feature branches must follow the convention: `feature/<agent_id>-<short-description>` (e.g., `feature/04-gradcam-service`).
- Commit messages must follow Conventional Commits:
  - `feat(ml): implement Grad-CAM hook on conv_head layer`
  - `fix(auth): correct JWT expiration calculation in auth route`
  - `docs(api): update OpenAPI schemas for screening endpoint`
- Never commit `.env`, credentials, model checkpoints (`*.pth`), or patient dataset files.

---

## 14. Testing Expectations

- No task may be marked `COMPLETED` without automated test validation.
- Unit tests must mock external dependencies (do not hit live external APIs in automated CI).
- AI inference tests must verify tensor dimensions, probability normalization, and non-zero gradient flow.
- All tests must pass before proposing code for integration.

---

## 15. Security Requirements

- Never store plaintext passwords or hardcode API keys/secrets in source code.
- Validate all incoming file uploads by checking magic bytes (header signatures) in addition to MIME extensions.
- Supabase `service_role` key must **NEVER** be embedded in the Flutter client.
- Enforce HTTPS and TLS for all client-server communications.
- Maintain immutable audit logging for all medical diagnosis operations.

---

## 16. Documentation Requirements

- All public functions and classes must include clear docstrings.
- Any API schema alteration must be reflected in `shared/api_contracts/` and `docs/API_DOCUMENTATION.md`.
- Architecture changes must be documented in `docs/architecture/`.

---

## 17. How Agents Communicate

Agents communicate asynchronously through:
1. **`docs/agents/WORK_LOG.md`:** The persistent ledger recording tasks, decisions, blockers, and handovers.
2. **Explicit Handover Notes:** When handing off deliverables to downstream agents.
3. **Formal Artifact Dependencies:** Contracts defined in `shared/api_contracts/` and `IMPLEMENTATION_PLAN.md`.

---

## 18. How to Update Completed Work

Whenever an agent finishes a task:
1. Run local tests to verify functionality.
2. Open `docs/agents/WORK_LOG.md`.
3. Append a new **Task Entry** using the standard template (Agent ID, Task, Files Created, Tests, Handovers).
4. Update task checkbox and status in `IMPLEMENTATION_PLAN.md`.
5. **Never delete previous work history.**

---

## 19. How to Report Blockers

If an agent encounters a missing dependency, environmental error, or architectural ambiguity:
1. Set the task status in `IMPLEMENTATION_PLAN.md` to `BLOCKED`.
2. Append a Task Entry in `docs/agents/WORK_LOG.md` detailing the blocker under the `### Blockers` header.
3. Notify Agent 00 (Lead Coordinator) in the `### Handover Notes` section.
4. Do **not** invent undocumented assumptions or silent workarounds.

---

## 20. How to Hand Over Work to Another Agent

When completing a task that unblocks another agent:
1. Detail the exact interfaces, file paths, and contracts created in `docs/agents/WORK_LOG.md`.
2. Include a `### Handover Notes` section directed specifically at the downstream agent (e.g., *"Handover to Agent 03: The ML module is available at `backend/app/ml/prediction.py`. It accepts a PIL image and returns `PredictionResult` Pydantic schema."*).
3. The incoming agent must review these notes and inspect the referenced code before beginning work.

