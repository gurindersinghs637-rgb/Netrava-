# NETRAVA workspace cleanup audit

18 November 2026 · Pre-cleanup baseline and approval proposal

## Inspection

The recursive inventory enumerated **40,679 files and 5,622 directories** below the workspace root, including installed dependencies and build outputs. It encountered two access errors at root `.pytest_cache` and `.pytest-temp-check`. Both directories are counted, and their contents are unknown. The inventory preceded this report and the baseline test runs. Source and artifact review focused on project-owned files, runtime references, and cleanup candidates. The workspace did not expose usable Git metadata, so this audit could not establish tracked status or rely on Git for recovery.

| Area | Role and preservation decision |
| --- | --- |
| `backend/app/` | FastAPI entry point `backend.app.main:app`, versioned routes, services, schemas, settings, templates and ML bridge |
| `ai_model/inference/` | Model loader, retinal preprocessing, predictor, and Grad-CAM targeting `conv_head` |
| `ai_model/checkpoint/best_efficientnet_b3_staged.pth` | Sole checkpoint found in first-party paths, 43,377,043 bytes. Backend settings and the inference loader resolve to the same file. |
| `ai_model/reference/NETRAVA_B3_Improved_Training.ipynb` | Training history and reference notebook |
| `ai_model/tests/data/` | Two canonical retinal PNGs used by tests or the verification script, plus a distinct sample Grad-CAM overlay |
| `backend/tests/`, `ai_model/tests/`, Flutter `test/` and `integration_test/` | Maintained test cases and fixtures |
| `frontend/flutter_app/`, `design_reference/` | Flutter client, native platform files, assets, and design references |
| `supabase/`, `shared/`, `scripts/` | Database migrations, archived migration, config and schema evidence, shared contracts, and verification tools |
| Root and component configuration | Preserve `.env`, env templates, `.gitignore`, `pyproject.toml`, `backend/pytest.ini`, requirements, dependency manifests and lockfiles, `.venv`, `.vscode`, and IDE configuration. |

The first-party scan found no standalone dataset directory, CSV, TSV, or Parquet file. Preserve any dataset or training material outside this workspace separately. The environment was checked through the application's resolved checkpoint setting without recording credential values.

## Deletion proposal

Approval applies only to the exact paths in this section. A pre-delete check should confirm that the paths still resolve inside the workspace, contain the reviewed artifacts, and have no reparse points. Preserve a reversible recovery copy or use a recoverable deletion mechanism, then rerun the baseline.

| Root pytest folders | Contents |
| --- | --- |
| `.pytest-active-signup`, `.pytest-ai-report-final`, `.pytest-ai-report-tmp`, `.pytest-password-recovery`, `.pytest-signup-20261114` | One `retina.png` each |
| `.pytest-continuation-1`, `.pytest-continuation-2`, `.pytest-continuation-final`, `.pytest-final-delivery`, `.pytest-readiness-final`, `.pytest-review-complete`, `.pytest-review-final`, `.pytest-review-verified`, `.pytest-temp-configured`, `.pytest-temp-final`, `.pytest-temp-mission`, `.pytest-temp-verified` | One `test_overlay.png` each, plus an empty directory from the invalid-checkpoint test |
| `.pytest-fixture-confirmed`, `.pytest-fixture-fix`, `.pytest-status-20261115` | Both images and an empty invalid-checkpoint test directory |

The eight root `retina.png` files share one SHA-256 digest. The generating test writes the resized derivative of `ai_model/tests/data/001639a390f0.png` to pytest's `tmp_path`. The fifteen root `test_overlay.png` files share a second digest and come from the predictor's overlay-save test. Both digests differ from all three canonical assets in `ai_model/tests/data/`. The 20 inspected root run folders contained no API exports, checkpoint files, or required application resources.

Additional exact targets:

- `backend/.pytest-ai-report` and `backend/.pytest_cache` contain standard pytest cache metadata and cached test IDs and failure records.
- `tmp/audit-pytest`, `tmp/audit-pytest-final`, `tmp/backend-report-pytest-temp`, and `tmp/report-master-pytest` contain the same two verified output types. `tmp/netrava-report-e2e.png` is byte-identical to the generated retinal derivative.
- Root `.coverage` is a generated historical coverage database. The audit does not use it to report current coverage.

The existing-artifact proposal covers **42 files in 26 directory targets and two standalone file targets**, totaling **2,033,972 bytes**. A fresh baseline pytest directory under `tmp/cleanup-audit-*` was created separately for this audit. It is outside these totals and can be retained for comparison.

## Deferred items

- Root `.pytest_cache` and `.pytest-temp-check` need successful inspection before any deletion decision.
- `frontend/flutter_app/lib.zip` contains 43 files, all byte-identical to the corresponding current frontend files. The two files named `NETRAVA Explainable AI System Architecture.png` and `NETRAVA Explainable AI System Architecture (1).png` in `docs/architecture/diagrams/` also match byte for byte. Consider retiring the archive and the suffixed diagram separately after confirming their backup or reference value.
- `backend/_test_import.py` and `backend/_test_rootimport.py` are manual diagnostic scripts outside standard pytest discovery. The former hardcodes a local path and later refers to an unbound `app` name. Retain both during cleanup.
- `output/apk/` contains three historical Android test builds totaling 529,757,470 bytes. `tmp/` also contains audit scripts, JSON and log evidence, and PDF outputs linked by prior reports. Retain these pending a separate retention review.
- `backend/model/README.md` documents the alternate deployment staging location. Keep it alongside the canonical development checkpoint path.

## Current and proposed structure

| Current | Proposed after approved cleanup |
| --- | --- |
| Root readmes, configuration, `.venv/`, `.vscode/`, and historical pytest runs | Existing entry points and local configuration, with the 20 confirmed root runs removed. Two unreadable folders remain pending inspection. |
| `backend/{app,tests,model}/` and two pytest caches | `backend/{app,tests,model}/`; routes stay in `app/api/v1/`, services in `app/services/`, and dependencies in `backend/requirements.txt`. |
| `ai_model/{checkpoint,inference,reference,tests}/` | Keep this cohesive ML package. Grad-CAM and preprocessing remain in `inference/` with the model loader and predictor. |
| `frontend/flutter_app/`, `design_reference/`, `docs/` | Keep Flutter, design assets, and documentation in their current locations. |
| `supabase/`, `shared/`, `scripts/`, `output/`, `tmp/` | Keep the existing structure and audit evidence, with only the explicitly listed generated files removed. |

This layout keeps established Python imports, checkpoint resolution, Flutter paths, and deployment references intact. Future pytest runs can use a fresh subdirectory under the already ignored `tmp/`. Root pytest collection currently defaults to `backend/tests`; pass both suites explicitly to include ML tests.

## Verification baseline

| Check | Actual result |
| --- | --- |
| Python environment and imports | Python 3.11.9. `pip check` reported no broken requirements. FastAPI imported and generated OpenAPI with 13 paths. |
| Checkpoint path | Resolved backend path exists and matches `ai_model.inference.model_loader.DEFAULT_CHECKPOINT_PATH`. |
| Backend and AI pytest | **184 passed**, 6 warnings. Covered CPU loading of the real EfficientNet-B3 checkpoint, retinal preprocessing and QC, predictions, Grad-CAM heatmap and overlay output, and local FastAPI behavior using isolated dependencies. |
| Flutter | **19 passed** with `flutter test --no-pub --reporter expanded`. Included client API contracts and technician and clinician workflows using fixtures. The installed SDK needed access to its external cache. |

Python emitted existing warnings for Pydantic's protected `model_` namespace, Starlette multipart and AnyIO imports, and deprecated Supabase dependency packages. Hosted Supabase, authenticated device-to-backend traffic, and post-cleanup verification remain pending. No application source was edited and no paths were deleted or moved during this audit.
