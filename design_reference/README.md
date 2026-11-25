# NETRAVA — Design Reference & UI/UX Catalog

**Design System Name:** Clinical Precision AI  
**Document Version:** 1.0.0  
**Target Viewport:** Mobile Smartphone (390 $\times$ 844 px fluid grid)  
**Lead Designer:** Agent 02 (UI/UX Designer)

---

## 1. Overview

This directory constitutes the **single source of truth** for all visual design, brand assets, color palettes, typography, spacing metrics, and screen layouts across the **NETRAVA** application ecosystem.

The design embodies modern clinical healthtech: rigorous, reassuring, and technologically advanced. It is tailored for field health workers, clinic technicians, and ophthalmologists performing rapid point-of-care screenings for Diabetic Retinopathy.

---

## 2. Directory Structure

```
design_reference/
├── README.md                      # This catalog guide
├── extracted/                     # Unpacked Stitch design export package
│   └── stitch_netrava_retinal_screening_app/
│       ├── 01_splash_welcome_screen/
│       │   ├── code.html          # HTML/Tailwind layout reference
│       │   └── screen.png         # High-resolution rendered mockup
│       ├── ... (14 screen folders)
│       └── clinical_precision_ai/
│           └── DESIGN.md          # Upstream token specification
│
├── design_system/                 # Documented token specifications
│   ├── COLORS.md                  # Semantic color palette & hex values
│   ├── TYPOGRAPHY.md              # Font families, sizes, weights, and metrics
│   ├── SPACING.md                 # 4-column layout, padding, margins, elevations
│   ├── ICONS.md                   # Clinical, optical, and navigational icons
│   ├── COMPONENTS.md              # Reusable atomic design component catalog
│   └── UI_GUIDELINES.md           # Handheld clinical ergonomics and safety
│
├── branding/                      # Brand assets and vectors
│   ├── logo/                      # NETRAVA dual-leaf emblem and typography
│   └── illustrations/             # Background waves, gradients, and accents
│
├── screenshots/                   # Categorized screen mockups & layout specs
│   ├── authentication/            # Screens 02, 03, 04, 05
│   ├── onboarding/                # Screens 01, 06
│   ├── dashboards/                # Screen 07 (Technician Dashboard)
│   ├── patient_management/        # Screens 08, 09
│   ├── image_capture/             # Screens 10, 11
│   ├── ai_analysis/               # Screen 12 (Grad-CAM viewer)
│   ├── results/                   # Screen 13 (Grading summary)
│   ├── reports/                   # Screen 14 (Referral & export)
│   └── README.md                  # Comprehensive 14-screen catalog
│
└── assets/                        # Shared fonts and icon binaries
    ├── fonts/                     # Poppins & Inter TTF font files
    ├── icons/
    └── images/
```

---

## 3. The 14 Clinical Screening Screens

| Screen # | Screen Name | Category | Primary Purpose |
|---|---|---|---|
| **01** | Splash Welcome Screen | Onboarding | App initialization, brand emblem, value pillars. |
| **02** | Get Started / Sign-in Options | Authentication | SSO gateway (Email, Google, Microsoft). |
| **03** | Login with Email | Authentication | Secure clinician/technician password authentication. |
| **04** | Sign in with Google | Authentication | Google Workspace OAuth flow. |
| **05** | Sign in with Microsoft | Authentication | Enterprise Azure AD / hospital SSO. |
| **06** | Select Your Role | Onboarding | Tri-role selector (Technician, Ophthalmologist, Admin). |
| **07** | Technician Dashboard | Dashboard | Screening queue, triage metrics, quick actions. |
| **08** | Patient Registration Intake | Patient Mgmt | New patient intake (Demographics, Diabetes history, HbA1c). |
| **09** | Patient Profile & History | Patient Mgmt | Longitudinal patient records and prior screenings. |
| **10** | Fundus Camera Live Capture | Image Capture | Live camera viewfinder with optic disc / macular alignment reticle. |
| **11** | Real-time Image Quality QC | Image Capture | Edge/server blur and illumination assessment. |
| **12** | AI Inference & Lesion Heatmap | AI Analysis | Dual-view fundus image with toggleable Grad-CAM heatmap overlay. |
| **13** | Clinical Report & Summary | Results | ICDR severity grading (0–4), confidence, risk assessment. |
| **14** | Export, Sync & Tele-Referral | Reports | PDF clinical report, tele-consultation dispatch. |

---

## 4. Design Guidelines for Frontend Developers

1. **Strict Palette Adherence:** Always import and utilize `AppColors` from `lib/core/theme/app_colors.dart`.
2. **Typography Scale:** Always use `AppTextStyles` from `lib/core/theme/app_text_styles.dart` to maintain proportional hierarchy.
3. **Medical Disclaimer Placement:** Every screen presenting clinical predictions must include the standard medical disclaimer.

