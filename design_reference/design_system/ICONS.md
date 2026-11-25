# NETRAVA Design System — Icons & Visual Symbols

**Design System:** Clinical Precision AI  
**Document Version:** 1.0.0  
**Specification File:** `design_reference/design_system/ICONS.md`

---

## 1. Iconography Principles

Icons in NETRAVA must communicate optical precision, medical authority, and instantaneous legibility under varied lighting conditions:
- **Geometry:** Rounded terminals with 1.8px to 2.0px stroke weight.
- **Visual Style:** Outlined / stroke-based for standard states; filled for active navigation states.
- **Standard Sizing:**
  - Micro: `16px` (Status indicators, inline badge prefixes).
  - Standard: `24px` (Form fields, list tile actions, app bar icons).
  - Prominent: `32px` (Viewfinder toggles, feature card highlights).
  - Hero: `48px` (Empty state illustrations, role selection cards).

---

## 2. Icon Inventory by Category

### 2.1 Navigation & System
- `arrow_back_ios_new_rounded`: Screen dismissal and backward traversal.
- `menu_rounded` / `tune_rounded`: Filter screening queues, adjust sensitivity.
- `notifications_none_rounded`: Tele-referral alerts and clinician feedback.
- `person_outline_rounded`: User profile and clinic settings.
- `search_rounded`: Patient name, MRN, and screening session lookup.

### 2.2 Ophthalmic & Camera Capture
- `visibility_outlined`: Eye examination icon, eye selection toggle (`OD` vs. `OS`).
- `center_focus_strong_rounded`: Optical reticle, macular centering, focus lock.
- `camera_alt_outlined`: Fundus image capture shutter.
- `flash_on_rounded` / `flash_off_rounded`: Illumination LED control.
- `flip_camera_ios_rounded`: Lens adapter orientation switch.

### 2.3 Quality Control (QC) & Diagnostics
- `check_circle_outline_rounded`: Image passed QC; screening valid.
- `warning_amber_rounded`: Borderline illumination or motion blur detected.
- `error_outline_rounded`: Image ungradable; mandatory retake prompt.
- `auto_awesome_rounded`: AI inference active; Grad-CAM generation.
- `layers_outlined`: Grad-CAM overlay toggle (Original vs. Heatmap vs. Blended).

### 2.4 Clinical Actions & Records
- `person_add_alt_1_rounded`: New patient intake registration.
- `history_rounded`: Longitudinal visit timeline.
- `description_outlined`: Clinical grading summary report.
- `picture_as_pdf_outlined`: Download / print official referral slip.
- `send_rounded`: Dispatch case to on-call ophthalmologist.
- `verified_user_outlined`: Clinician signature lock.

---

## 3. Eye Designation Tags (`OD` vs. `OS`)

To avoid catastrophic medical misidentification, eye designations must be rendered as prominent segmented pill controls:
- **OD (Oculus Dexter — Right Eye):** Green active badge (`#005D49`).
- **OS (Oculus Sinister — Left Eye):** Green active badge (`#005D49`).
- **Inactive Eye:** Soft mint container (`#E6F4EE`) with slate text (`#71827C`).

