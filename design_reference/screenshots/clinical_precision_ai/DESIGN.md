---
name: Clinical Precision AI
colors:
  surface: '#e5fff7'
  surface-dim: '#c6dfd8'
  surface-bright: '#e5fff7'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#e0f9f1'
  surface-container: '#daf3ec'
  surface-container-high: '#d4eee6'
  surface-container-highest: '#cfe8e0'
  on-surface: '#081f1b'
  on-surface-variant: '#3e4944'
  inverse-surface: '#1e3430'
  inverse-on-surface: '#ddf6ef'
  outline: '#6e7a74'
  outline-variant: '#bdc9c3'
  surface-tint: '#006b54'
  primary: '#005d49'
  on-primary: '#ffffff'
  primary-container: '#08785f'
  on-primary-container: '#a1fddd'
  inverse-primary: '#7cd7ba'
  secondary: '#006b55'
  on-secondary: '#ffffff'
  secondary-container: '#87f3d2'
  on-secondary-container: '#007059'
  tertiary: '#485550'
  on-tertiary: '#ffffff'
  tertiary-container: '#606d68'
  on-tertiary-container: '#e0eee8'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#98f4d5'
  primary-fixed-dim: '#7cd7ba'
  on-primary-fixed: '#002118'
  on-primary-fixed-variant: '#00513f'
  secondary-fixed: '#8af6d4'
  secondary-fixed-dim: '#6ddab9'
  on-secondary-fixed: '#002118'
  on-secondary-fixed-variant: '#00513f'
  tertiary-fixed: '#d8e6e0'
  tertiary-fixed-dim: '#bccac4'
  on-tertiary-fixed: '#121e1b'
  on-tertiary-fixed-variant: '#3d4945'
  background: '#e5fff7'
  on-background: '#081f1b'
  surface-variant: '#cfe8e0'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 26px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 26px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 17px
    fontWeight: '600'
    lineHeight: 22px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.04em
  mono-metric:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '700'
    lineHeight: 26px
    letterSpacing: -0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  margin: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.25rem
  space-xl: 1.75rem
---

## Brand & Style

This design system embodies modern clinical healthtech: rigorous, reassuring, and technologically advanced. It is tailored for ophthalmologists, clinicians, and field health workers performing rapid AI-assisted screenings for Diabetic Retinopathy.

The design language balances high-stakes medical credibility with approachable efficiency:
- **Clinical Rigor & Trust:** Prioritizes optical clarity, diagnostic confidence, and clear triage hierarchies without visual clutter or alarmist tones.
- **Modern Minimal Tech:** Uses airy surfaces, crisp data visualizations, and soft containment layers to prevent cognitive fatigue during extended mobile screening sessions.
- **Diagnostic Focus:** High contrast is strictly applied to retinal scans, severity stages, and critical confidence intervals, ensuring diagnostic elements stand out against calm, neutral backdrops.

## Colors

The palette establishes an authoritative, calming clinical baseline that supports rapid parsing of patient results:

- **Primary (`#08785F`):** Deep surgical teal/green. Used for primary CTAs, active screening navigation, high-level headers, and high-confidence metrics.
- **Secondary (`#149477`):** Vibrant clinical emerald. Used for interactive states, focused items, secondary action surfaces, and subtle visual indicators.
- **Tertiary (`#E6F4EE`):** Soft mint tint. Used for badge fills, card highlights, progress bars, and tinted selection containers.
- **Neutral Surface & Background (`#F5FAF7`):** A soft, pale eucalyptus canvas that eliminates clinical glare while remaining clean.
- **Surface Elevation (`#FFFFFF`):** Pure white used for elevated cards, modal sheets, and camera viewfinder containment.
- **Typography Neutrals:** Primary dark text (`#253B36`) provides high-contrast legibility; secondary neutral (`#71827C`) handles metadata, units, and timestamps.
- **Clinical Semantic Statuses:**
  - **Success / Normal Retinopathy (`#21A36D`):** Non-referable, clear vessels, low risk.
  - **Warning / Moderate Retinopathy (`#E9A23B`):** Borderline confidence, review recommended, mild microaneurysms.
  - **Critical / Severe Retinopathy (`#D9534F`):** Proliferative DR, immediate referral, high-urgency detection.

## Typography

The type scale is standardized around Inter to guarantee absolute legibility under varied mobile screen illuminations and clinical field conditions.

- **Numbers and AI Metrics:** Tabular figures (`tnum`) should be enabled for confidence scores, grading values (e.g., ETDRS Scale), and scan metadata.
- **Hierarchy Rules:** Diagnoses and patient identity use `headline-lg` and `headline-md`. Clinical tag titles and section divisions rely on uppercase `label-sm` with slight tracking to ensure immediate categorization.
- **Readability Guarantees:** Body copy is restricted to standard weights (400 and 600) to maintain crisp edges on high-DPI smartphone displays (such as 390x844px viewports).

## Layout & Spacing

Designed specifically for handheld clinical operations on standard mobile displays (390x844 px), the layout follows a compact 4-column fluid mobile grid.

- **Margins & Safe Zones:** Canvas outer margins are fixed at `1rem` (16px), matching standard handheld tap areas while reserving full screen real estate for high-resolution retinal fundus visualizations.
- **Thumb-Zone Optimization:** Critical action buttons (Capture Fundus, Process AI, Confirm Assessment) are pinned within a persistent floating bottom navigation dock, padded by `space-md` with native mobile safe-area insets.
- **Information Architecture Rhythm:** Card stacking utilizes `space-md` (16px) separation. Internal card nesting adheres to `space-sm` (8px) for related metadata groups and `space-md` for distinct clinical findings.

## Elevation & Depth

Visual hierarchy leverages crisp surface layering combined with ambient, tinted shadows to prevent harsh contrast lines:

- **Surface 0 (Background Canvas):** Tinted medical mist (`#F5FAF7`), entirely flat.
- **Surface 1 (Standard Card & Panel):** Pure white (`#FFFFFF`) with an ultra-soft teal-tinted shadow: `0 4px 20px -2px rgba(8, 120, 95, 0.05), 0 2px 6px -1px rgba(37, 59, 54, 0.03)`.
- **Surface 2 (Floating Action Docks & Sheets):** Elevated white with an extended diffused shadow: `0 12px 32px -4px rgba(8, 120, 95, 0.12), 0 4px 12px -2px rgba(37, 59, 54, 0.06)`.
- **Retinal Imaging Viewport:** Encapsulated in a deep aperture ring using an inset shadow: `inset 0 0 0 1px rgba(8, 120, 95, 0.12)`, grounding high-contrast fundus photography against the light background.

## Shapes

The interface balances soft tactile warmth with clean clinical geometry. Structural cards adopt an expressive `rounded-2xl` (16px) silhouette to feel modern, safe, and approachable, while functional data elements tighten up:

- **Diagnostic Cards & Containers:** 16px (`rounded-2xl`) border radius.
- **Interactive Inputs & Action Buttons:** 12px to 14px radius for comfortable thumb targeting.
- **Status Tags & Medical Badges:** Full pill radius (9999px) to communicate atomic, non-editable clinical classifications.
- **Viewfinder Reticle / Fundus Mask:** Circular (50%) to mirror standard ophthalmic lens geometry.

## Components

### Buttons
- **Primary:** Background `#08785F`, text `#FFFFFF`, 14px radius, 52px height for mobile hit-target confidence. Active states shift to `#149477`.
- **Secondary / Ghost:** Background `#E6F4EE`, text `#08785F`, borderless, 52px height.
- **Destructive:** Background `#D9534F` with white label for irrevocable actions (e.g., delete patient dataset).

### Medical Badge Tags
- **Construction:** Height 24px, pill-shaped, horizontal padding 10px, typography `label-sm`.
- **Severity Variations:**
  - *No DR / Normal:* Background `#E6F4EE`, text `#21A36D`.
  - *Mild / Moderate NPDR:* Background `#FEF6EB`, text `#E9A23B`.
  - *Severe NPDR / PDR:* Background `#FDEEEE`, text `#D9534F`.
  - *AI Confidence:* Background `#E6F4EE`, text `#08785F`, accompanied by a leading 6px confidence indicator dot.

### Diagnostic Cards
- **Base Style:** `#FFFFFF` background, `rounded-2xl` (16px), 16px internal padding, ambient teal-tinted shadow.
- **Header:** Patient demographic data / screening timestamp with a status badge floated top-right.
- **Content Splitting:** Left-hand micro thumbnail of fundus scan (48x48px, rounded 8px), right-hand clinical prediction with confidence metric.

### Retinal Fundus Viewport & Heatmap UI
- **Canvas:** Circular crop container bordered by `#E6F4EE` 2px outline, dark aperture backing (`#0A1210`) for contrast during alignment.
- **Overlay HUD:** Monospace coordinates, crosshair guide, and toggleable AI lesion heatmaps (grad-CAM red/yellow zones) with 85% opacity overlays.

### Inputs & Selection Controls
- **Text Inputs:** Height 48px, background `#FFFFFF`, border 1.5px solid `#E6F4EE`, text `#253B36`. Focus state transitions to a solid 1.5px `#08785F` border with zero layout shift.
- **Selection Pills (OD / OS - Right Eye / Left Eye):** Segmented control with equal 50% split. Active segment receives `#08785F` background and white text; inactive sits on `#E6F4EE` with `#71827C` text.