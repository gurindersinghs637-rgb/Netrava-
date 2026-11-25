# NETRAVA Design System — Spacing, Elevation & Layout

**Design System:** Clinical Precision AI  
**Document Version:** 1.0.0  
**Specification File:** `design_reference/design_system/SPACING.md`

---

## 1. Mobile Grid & Canvas Metrics

NETRAVA is engineered for one-handed and two-handed clinical field operations on standard mobile displays (reference: $390 \times 844$ px viewport, scalable to 360–440 px widths):

- **Grid System:** 4-column fluid grid.
- **Outer Canvas Margins:** Fixed at `16px` (`1rem`).
- **Gutter Width:** Fixed at `16px` (`1rem`).
- **Safe Area Insets:** Strict adherence to mobile top notches and bottom home indicators via Flutter `SafeArea`.
- **Thumb-Zone Optimization:** Critical action buttons (Capture Scan, Process AI, Confirm Assessment) are pinned within persistent floating bottom action docks.

---

## 2. Spacing Scale

| Token Name | Value (px) | Tailwind Equiv. | Usage Guidelines |
|---|---|---|---|
| `space-xxs` | 2px | `0.125rem` | Fine hair dividers, sub-pixel accent bars. |
| `space-xs` | 4px | `0.25rem` | Spacing between icon and adjacent label, tag inner vertical padding. |
| `space-sm` | 8px | `0.5rem` | Gap between stacked metadata rows, chip horizontal spacing. |
| `space-md` | 16px | `1.0rem` | Standard container padding, card vertical stacking distance, form gap. |
| `space-lg` | 20px | `1.25rem` | Card internal padding for primary diagnostic containers. |
| `space-xl` | 24px | `1.5rem` | Section header to content spacing, modal sheet padding. |
| `space-2xl` | 32px | `2.0rem` | Top margin for major views, distance between feature groups. |
| `space-3xl` | 48px | `3.0rem` | Splash screen vertical separators. |

---

## 3. Shapes & Border Radiuses

The interface combines clinical precision with ergonomic softness:

| Shape Token | Radius (px) | Usage Guidelines |
|---|---|---|
| `rounded-sm` | 4px | Progress bars, small checkboxes, accent indicator chips. |
| `rounded-md` | 8px | Micro thumbnails (48x48px scans), secondary action buttons. |
| `rounded-lg` | 12px | Text inputs, dropdown selection fields. |
| `rounded-xl` | 14px | Primary action buttons (52px height). |
| `rounded-2xl` | 16px | Standard diagnostic cards, modal dialogs, bottom sheets. |
| `rounded-full`| 9999px | ICDR severity badges, status tags, toggle pills, circular icon buttons. |
| `circular` | 50% | Retinal fundus camera viewfinder reticle. |

---

## 4. Elevation & Shadow Tiers

Visual hierarchy is maintained through subtle, tinted shadows rather than harsh grey drop shadows:

### Tier 0: Flat Canvas (`Surface 0`)
- **Background:** `#F5FAF7`
- **Shadow:** None (`elevation: 0`).

### Tier 1: Elevated Diagnostic Card (`Surface 1`)
- **Background:** `#FFFFFF`
- **Border:** 1px solid `#E0ECE6`
- **Shadow:** `box-shadow: 0 4px 20px -2px rgba(8, 120, 95, 0.05), 0 2px 6px -1px rgba(37, 59, 54, 0.03)`
- **Flutter:**
  ```dart
  BoxShadow(
    color: const Color(0xFF08785F).withOpacity(0.05),
    blurRadius: 20,
    offset: const Offset(0, 4),
  )
  ```

### Tier 2: Floating Bottom Action Dock & Modal Sheets (`Surface 2`)
- **Background:** `#FFFFFF`
- **Shadow:** `box-shadow: 0 12px 32px -4px rgba(8, 120, 95, 0.12), 0 4px 12px -2px rgba(37, 59, 54, 0.06)`
- **Flutter:**
  ```dart
  BoxShadow(
    color: const Color(0xFF08785F).withOpacity(0.12),
    blurRadius: 32,
    offset: const Offset(0, -4),
  )
  ```

### Tier 3: Retinal Viewfinder Ring
- **Border:** 2px solid `#E6F4EE`
- **Inner Shadow:** `inset 0 0 0 1px rgba(8, 120, 95, 0.12)`
- **Background:** `#0A1210` (Deep aperture dark ground for alignment contrast).

