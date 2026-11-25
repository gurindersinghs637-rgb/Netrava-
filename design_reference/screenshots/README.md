# NETRAVA — Complete 14-Screen UI/UX Specification Catalog

**Design System:** Clinical Precision AI  
**Document Version:** 1.0.0  
**Specification File:** `design_reference/screenshots/README.md`  
**Lead Designer:** Agent 02 (UI/UX Designer)

---

## Screen 01: Splash Welcome Screen

- **Directory:** `design_reference/screenshots/01_splash_welcome_screen/`
- **Visual Reference:** `screen.png` | **Code Reference:** `code.html`
- **Category:** Onboarding
- **Purpose:** Introduce the NETRAVA system, establish brand identity, highlight three clinical value pillars, and route users to authentication.
- **Layout:** Centered vertical column constrained to max 440px width; ambient top-right help button; bottom organic wave layer.
- **Components:**
  - `NetravaLogo`: Dual-leaf vector emblem, brand title ("NETRAVA"), tagline ("SEE. DETECT. EXPLAIN.").
  - Headline: "Welcome to NETRAVA" with green brand highlight.
  - Subtitle: "Your intelligent companion for retinal screening."
  - Auth Options: "Continue with Email", "Continue with Google", "Continue with Microsoft".
  - Divider: Horizontal line with centered "OR".
  - Feature Highlights: Early Detection, AI-Powered Analysis, Healthier Communities.
- **Colors:** Canvas `#F5FAF7`, Primary Green `#075E4D`, Waves `#075E4D` / `#23846C` / `#5EB395`.
- **Typography:** Brand Title Poppins 32px Bold; Subtitle Inter 15px Regular; Buttons Inter 15px Bold.
- **Interactions:** Tap "Continue with Email" -> Navigates to Screen 03; Tap "Log in →" -> Navigates to Screen 03.
- **API Dependencies:** None.

---

## Screen 02: Get Started / Sign-In Options

- **Directory:** `design_reference/screenshots/02_get_started_sign_in_options/`
- **Visual Reference:** `screen.png` | **Code Reference:** `code.html`
- **Category:** Authentication
- **Purpose:** Serve as a clean authentication hub for health system SSO and email credentials.
- **Layout:** Card-based modal presentation on mint background.
- **Components:**
  - Header with ophthalmic icon badge.
  - Triple SSO action stack (Email, Google Workspace, Azure AD / Microsoft Health).
  - Terms of service and clinical privacy policy disclaimer footer.
- **Colors:** Surface `#FFFFFF`, Primary `#005D49`, Border `#E0ECE6`.
- **Interactions:** Tap provider button -> Launches corresponding auth flow.
- **API Dependencies:** OAuth identity provider callback URL.

---

## Screen 03: Login with Email

- **Directory:** `design_reference/screenshots/03_login_with_email/`
- **Visual Reference:** `screen.png` | **Code Reference:** `code.html`
- **Category:** Authentication
- **Purpose:** Enable registered technicians and clinicians to authenticate using their verified email and password.
- **Layout:** Form stack with back navigation button, heading, input fields, password toggle, and primary CTA.
- **Components:**
  - Email input field with mail icon.
  - Password input field with visibility toggle.
  - "Forgot Password?" text link.
  - "Log In" primary 54px button.
- **Colors:** Input fill `#FFFFFF`, Input border `#E0ECE6`, Focus border `#005D49`.
- **Interactions:** Submitting valid credentials -> Navigates to Screen 06 (Role Selection) or Screen 07 (Dashboard).
- **API Dependencies:** `POST /api/v1/auth/login`.

---

## Screen 04: Sign in with Google

- **Directory:** `design_reference/screenshots/04_sign_in_with_google/`
- **Visual Reference:** `screen.png` | **Code Reference:** `code.html`
- **Category:** Authentication
- **Purpose:** Seamless Google Workspace OAuth integration for clinical partners.
- **Layout:** Standard OAuth consent card.
- **API Dependencies:** Supabase GoTrue Google OAuth provider.

---

## Screen 05: Sign in with Microsoft

- **Directory:** `design_reference/screenshots/05_sign_in_with_microsoft/`
- **Visual Reference:** `screen.png` | **Code Reference:** `code.html`
- **Category:** Authentication
- **Purpose:** Enterprise hospital integration supporting Azure Active Directory / Microsoft Entra ID.
- **Layout:** Healthcare enterprise sign-in dialog.
- **API Dependencies:** Supabase GoTrue Azure OAuth provider.

---

## Screen 06: Select Your Role

- **Directory:** `design_reference/screenshots/06_select_your_role/`
- **Visual Reference:** `screen.png` | **Code Reference:** `code.html`
- **Category:** Onboarding / Role Gateway
- **Purpose:** Present authorized system roles to the authenticated user and route to the corresponding workspace.
- **Layout:** Vertical card stack displaying 3 selectable roles.
- **Components:**
  - Field Technician Card: "Capture scans, real-time QC, rapid triage screening."
  - Ophthalmologist Card: "Review AI diagnoses, inspect Grad-CAM, sign clinical reports."
  - Administrator Card: "Clinic management, staff accounts, system audit logs."
- **Colors:** Unselected cards `#FFFFFF`; Selected card `#E6F4EE` with `#005D49` 2px border.
- **Interactions:** Selecting role updates user profile and transitions to Screen 07.
- **API Dependencies:** `POST /api/v1/auth/role`.

---

## Screen 07: Technician Dashboard

- **Directory:** `design_reference/screenshots/07_technician_dashboard/`
- **Visual Reference:** `screen.png` | **Code Reference:** `code.html`
- **Category:** Dashboard
- **Purpose:** Primary workstation for field technicians managing patient queues and daily screening throughput.
- **Layout:** Top clinic header, summary metric pills, quick action bar, and scrollable recent patient list.
- **Components:**
  - Metric Pills: "Today's Screenings: 24", "Pending AI Review: 3", "Urgent Referrals: 2".
  - Quick Action Button: "+ New Screening Intake" (Primary Green 54px).
  - Search & Filter Bar: Search by Patient Name or MRN.
  - Patient Screening Cards: Demographic details, eye scanned (OD/OS), ICDR badge, review status.
- **Colors:** Canvas `#F5FAF7`, Card White `#FFFFFF`, Accent Mint `#E6F4EE`.
- **Interactions:** Tap "+ New Screening" -> Screen 08; Tap Patient Card -> Screen 09.
- **API Dependencies:** `GET /api/v1/screenings`, `GET /api/v1/screenings/metrics`.

---

## Screen 08: Patient Registration Intake Form

- **Directory:** `design_reference/screenshots/08_patient_registration_intake_form/`
- **Visual Reference:** `screen.png` | **Code Reference:** `code.html`
- **Category:** Patient Management
- **Purpose:** Rapid clinical data entry for new diabetic patients prior to optical imaging.
- **Layout:** Grouped multi-section form with floating bottom submit action.
- **Components:**
  - Section 1: Demographics (Full Name, National ID / MRN, Age, Gender, Phone).
  - Section 2: Diabetic History (Diabetes Type: Type 1 / Type 2 / Gestational, Duration in Years).
  - Section 3: Vitals & Lab (Latest HbA1c %, Blood Pressure mmHg, Insulin Dependent toggle).
  - Submit CTA: "Proceed to Retinal Capture →".
- **Interactions:** Validates required fields, persists draft locally, and navigates to Screen 10.
- **API Dependencies:** `POST /api/v1/patients`.

---

## Screen 09: Patient Profile & Medical History

- **Directory:** `design_reference/screenshots/09_patient_profile_medical_history/`
- **Visual Reference:** `screen.png` | **Code Reference:** `code.html`
- **Category:** Patient Management
- **Purpose:** Display comprehensive longitudinal history, previous retinal scans, and disease progression.
- **Layout:** Patient banner with demographic chips, systemic indicators card, and chronological screening timeline.
- **Components:**
  - Patient Header: Name, MRN, Age, Gender, Primary Clinic.
  - Vitals Summary: Current HbA1c, Diabetes Duration, Systemic Risk Score.
  - Historical Screening Timeline: Dates, OD/OS thumbnails, past DR grades, attending clinicians.
  - Action Button: "Start New Screening Session".
- **API Dependencies:** `GET /api/v1/patients/{id}`, `GET /api/v1/patients/{id}/history`.

---

## Screen 10: Fundus Camera Live Capture & Optical Alignment

- **Directory:** `design_reference/screenshots/10_fundus_camera_live_capture_optical_alignment/`
- **Visual Reference:** `screen.png` | **Code Reference:** `code.html`
- **Category:** Image Capture
- **Purpose:** Guide the technician during optical alignment and acquire high-resolution fundus images.
- **Layout:** Full-screen optical viewfinder with HUD overlays and floating camera controls.
- **Components:**
  - Circular Viewfinder Reticle: 50% circular mask bordered in mint with centered crosshairs.
  - Alignment Indicators: Optic disc positioning ring (nasal) and macula target (center).
  - Eye Toggle Segment: Prominent pill switcher between "OD (Right Eye)" and "OS (Left Eye)".
  - Shutter Controls: Large circular shutter button (72px), flash toggle, focus lock, gallery import.
- **Colors:** Deep dark viewport `#0A1210`, Reticle `#E6F4EE`, Active Eye `#005D49`.
- **Interactions:** Tap Shutter -> Captures frame, crops to square, navigates to Screen 11.
- **API Dependencies:** None (Hardware camera).

---

## Screen 11: Real-Time Image Quality QC Assessment

- **Directory:** `design_reference/screenshots/11_real_time_image_quality_qc_assessment/`
- **Visual Reference:** `screen.png` | **Code Reference:** `code.html`
- **Category:** Image Capture
- **Purpose:** Automatically evaluate captured scan for sharpness, pupil illumination, and field-of-view centering before triggering AI inference.
- **Layout:** Central scan preview with diagnostic QC scorecard and dual action buttons.
- **Components:**
  - Captured Image Card: High-resolution preview of fundus photograph.
  - QC Scorecard:
    - Focus / Clarity: Passed (Laplacian variance score).
    - Illumination / Glare: Optimal (Histogram check).
    - Field Centering: Valid (Optic disc and macula detected).
  - Overall QC Rating: "GRADABLE SCAN (Confidence: 98%)".
  - Action Buttons: "Retake Scan" (Outlined) vs. "Run AI Diagnostic →" (Primary Green).
- **Interactions:** Tap "Run AI Diagnostic" -> Sends image to backend, opens Screen 12.
- **API Dependencies:** `POST /api/v1/screenings/qc`.

---

## Screen 12: AI Diagnostic Inference & Lesion Heatmap (Grad-CAM)

- **Directory:** `design_reference/screenshots/12_ai_diagnostic_inference_lesion_heatmap/`
- **Visual Reference:** `screen.png` | **Code Reference:** `code.html`
- **Category:** AI Analysis & Explainability
- **Purpose:** Present the deep learning severity prediction paired with spatial Grad-CAM explanations.
- **Layout:** Top diagnosis card, interactive fundus/heatmap dual-layer viewport, and layer controls.
- **Components:**
  - Severity Banner: Predicted Grade (e.g., "MODERATE NPDR"), ICDR Class, Model Confidence (`94.8%`).
  - Interactive Retinal Viewport:
    - Fundus photo with blended Jet heatmap overlay ($\alpha=0.40$).
    - Lesion focus indicators (Microaneurysms, hemorrhages, hard exudates).
  - Layer Control Dock:
    - "Original Fundus" toggle.
    - "Grad-CAM Heatmap" toggle.
    - Opacity Slider (0% to 100%).
  - Medical Safety Disclaimer: "Heatmap highlights regions influencing AI scoring; clinical validation required."
  - Action Button: "Generate Clinical Summary →".
- **Colors:** Severe Badge `#FEF0E0` / `#E07A1F`, Viewport `#FFFFFF`.
- **Interactions:** Dragging opacity slider dynamically adjusts overlay transparency.
- **API Dependencies:** `POST /api/v1/predict`.

---

## Screen 13: Clinical Report & Grading Summary

- **Directory:** `design_reference/screenshots/13_clinical_report_grading_summary/`
- **Visual Reference:** `screen.png` | **Code Reference:** `code.html`
- **Category:** Results & Clinical Summary
- **Purpose:** Comprehensive clinical summary suitable for patient counseling or ophthalmologist consultation.
- **Layout:** Scrollable medical report sheet with dual-eye comparisons (OD & OS).
- **Components:**
  - Patient & Visit Header: Demographic details, date, technician ID.
  - Bilateral Retinal Comparison: Right Eye (OD) scan & grade vs. Left Eye (OS) scan & grade.
  - Probability Breakdown: Bar chart showing probabilities across all 5 classes.
  - Clinical Recommendations: Recommended follow-up interval (e.g., "Ophthalmologist review within 30 days").
  - Ophthalmologist Review Section: Notes field, grade adjustment dropdown, digital signature line.
- **API Dependencies:** `GET /api/v1/screenings/{id}/report`, `POST /api/v1/screenings/{id}/review`.

---

## Screen 14: Export, Sync & Tele-Ophthalmology Referral

- **Directory:** `design_reference/screenshots/14_export_sync_tele_ophthalmology_referral/`
- **Visual Reference:** `screen.png` | **Code Reference:** `code.html`
- **Category:** Reports & Tele-health
- **Purpose:** Generate official PDF reports, dispatch urgent tele-referrals to retinal specialists, and synchronize records.
- **Layout:** Export card with action tiles and referral confirmation status.
- **Components:**
  - Export Options:
    - "Download Clinical PDF Report" (Standard 2-page clinical screening slip).
    - "Share via Secure Email / Hospital EMR".
  - Tele-Ophthalmology Dispatch:
    - Select On-Call Specialist / Vitreoretinal Clinic.
    - Urgency Level Selector: Routine / Priority / Immediate.
    - "Dispatch Referral Case" CTA.
  - Cloud Sync Status: "Record Synchronized with Central Supabase Cloud".
- **API Dependencies:** `POST /api/v1/reports/pdf`, `POST /api/v1/referrals`.

