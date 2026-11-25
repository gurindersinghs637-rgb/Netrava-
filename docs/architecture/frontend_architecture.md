# NETRAVA — Deep-Dive Frontend Architecture

**Component:** Flutter Mobile Client (`frontend/flutter_app`)  
**Document Version:** 1.0.0  
**Authority:** Agent 01 (Frontend Architect)

---

## 1. Clean Architecture & Feature Modularization

The Flutter client adheres to **Clean Architecture** organized by domain features:

```
lib/
├── app/                  # Application bootstrap, AppRoutes, global providers
├── core/                 # Shared foundations
│   ├── constants/        # Route constants, API endpoints, error strings
│   ├── network/          # Dio client, interceptors, error mapping
│   ├── storage/          # Encrypted SharedPreferences / SQLite offline db
│   └── theme/            # AppColors, AppTextStyles, AppTheme
├── shared/               # Reusable UI components (Buttons, Badges, Loaders)
└── features/             # Feature slices (Presentation, Domain, Data)
    ├── authentication/
    ├── role_selection/
    ├── dashboard/
    ├── patients/
    ├── image_capture/
    ├── image_quality/
    ├── ai_analysis/
    ├── results/
    ├── reports/
    └── profile/
```

Each feature slice contains:
- `presentation/`: Screens, controllers/notifiers, and feature-specific widgets.
- `domain/`: Business entities and use-case interfaces.
- `data/`: Repositories and REST API data sources.

---

## 2. State Management Architecture

NETRAVA utilizes **Riverpod** (or structured **ChangeNotifier Provider**):
- **AuthNotifier:** Tracks JWT session, active user profile, and assigned role.
- **PatientNotifier:** Manages active screening patient, demographic intake form validation, and recent screening history.
- **ScreeningCaptureNotifier:** Controls camera controller, eye selection (`OD`/`OS`), flash/focus states, and captured image buffer.
- **AIAnalysisNotifier:** Manages inference request status (`idle`, `processing`, `completed`, `error`), predicted ICDR grade, and Grad-CAM opacity layer state.

---

## 3. Offline Resilience & Sync Flow

1. Technician completes patient intake and captures fundus scans in remote clinic without network connectivity.
2. The app persists the patient record and encrypted image files into a local SQLite database (`pending_sync` queue).
3. The dashboard displays an amber `Sync Pending (N)` badge.
4. When network connectivity is restored (monitored via `connectivity_plus`), a background sync worker sequentially uploads records to the FastAPI backend and refreshes the local cache.

