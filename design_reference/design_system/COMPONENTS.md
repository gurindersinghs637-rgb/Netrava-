# NETRAVA Design System — Component Catalog

**Design System:** Clinical Precision AI  
**Document Version:** 1.0.0  
**Specification File:** `design_reference/design_system/COMPONENTS.md`

---

## 1. Primary Action Buttons

Buttons provide tactile, confident feedback with minimum 48px hit areas for field use:

### 1.1 Primary CTA Button
- **Height:** 52px (standard) / 54px (prominent).
- **Border Radius:** 14px (`rounded-xl`).
- **Background:** `AppColors.primaryGreen` (`#005D49` / `#08785F`).
- **Label Style:** White, 16px, Inter Bold (700), centered.
- **Elevation:** Tier 1 soft shadow (`0 4px 14px rgba(8, 120, 95, 0.20)`).
- **Disabled State:** Background `#CFE8E0`, text `#8FA39C`.

### 1.2 Secondary / Outlined Button
- **Height:** 52px.
- **Border Radius:** 14px.
- **Background:** Transparent or `AppColors.accentMint` (`#E6F4EE`).
- **Border:** 1.5px solid `AppColors.primaryGreen`.
- **Label Style:** `AppColors.primaryGreen`, 16px, Inter SemiBold (600).

### 1.3 Social & Enterprise SSO Buttons
- **Options:** "Continue with Email", "Continue with Google", "Continue with Microsoft".
- **Height:** 52px.
- **Border Radius:** 16px.
- **Background:** `#FFFFFF`.
- **Border:** 1.2px solid `#E0ECE6`.
- **Leading Icon:** SVG / PNG brand asset (20px width).
- **Elevation:** 1px soft ambient drop shadow.

---

## 2. Medical Badge Tags (ICDR Severity)

Atomic clinical indicators communicating non-editable diagnostic classifications:
- **Height:** 24px to 28px.
- **Border Radius:** Full Pill (`9999px`).
- **Padding:** 8px horizontal, 4px vertical.
- **Typography:** `label-sm` (11px, Inter Bold, uppercase, +0.04em letter spacing).

### Variants
1. **No DR / Normal:**
   - Background: `#E6F4EE`
   - Label Color: `#21A36D`
   - Leading Element: Green 6px solid circular pulse dot.
2. **Mild NPDR:**
   - Background: `#FEF6EB`
   - Label Color: `#E9A23B`
3. **Moderate NPDR:**
   - Background: `#FEF0E0`
   - Label Color: `#E07A1F`
4. **Severe NPDR:**
   - Background: `#FDEEEE`
   - Label Color: `#D9534F`
5. **Proliferative DR (PDR):**
   - Background: `#FFDAD6`
   - Label Color: `#BA1A1A`
   - Text: "PROLIFERATIVE (URGENT)"

---

## 3. Diagnostic Patient & Screening Cards

Container cards displaying patient summaries, triage status, and scan thumbnails:
- **Background:** `#FFFFFF` (`surface-container-lowest`).
- **Border Radius:** 16px (`rounded-2xl`).
- **Padding:** 16px internal padding.
- **Border:** 1px solid `#E0ECE6`.
- **Layout:**
  - Header Row: Patient Name (`headline-sm`, 17px Bold), MRN, and floated ICDR severity badge.
  - Middle Row: Left-hand fundus scan thumbnail (48x48px, 8px radius); right-hand metrics (AI Confidence score, screening date).
  - Footer Action: "View Analysis →" or "Ophthalmologist Review Pending".

---

## 4. Retinal Fundus Viewport & Heatmap Viewer

The core diagnostic visualization component:
- **Geometry:** Circular aperture (50% radius mask) with 2px `#E6F4EE` containment border.
- **Backing:** Deep dark aperture (`#0A1210`) ensuring high-contrast fundus visualization.
- **Layer 1 (Base):** High-resolution retinal fundus photo ($300 \times 300$ or original capture).
- **Layer 2 (Grad-CAM Overlay):** Jet pseudo-colored activation heatmap with dynamic opacity slider (0.0 to 1.0, default 0.40).
- **HUD Reticle (In Camera View):** Centered dashed crosshairs indicating macular positioning and concentric optic disc alignment guide.
- **Interactive Controls:** Floating tool dock at bottom providing:
  - Original Image Toggle.
  - Heatmap Overlay Toggle.
  - Side-by-Side Dual View.
  - Full-Screen Pinch-to-Zoom.

---

## 5. Form Inputs & Selection Controls

- **Text Inputs:**
  - Height: 48px to 52px.
  - Background: `#FFFFFF`.
  - Border: 1.5px solid `#BDC9C3`.
  - Focus State: Border transitions to 2px solid `AppColors.primaryGreen` (`#005D49`) with subtle mint halo.
  - Prefix Icon: Optical/clinical icon in primary green.
- **Segmented Eye Selection (OD / OS):**
  - Container: 44px height, `#E6F4EE` background, 12px border radius.
  - Active Segment: `#005D49` fill, white bold label, animated slide transition.
  - Inactive Segment: Transparent, slate text (`#3E4944`).

