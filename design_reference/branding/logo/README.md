# NETRAVA Branding — Logo & Emblem Specification

**File:** `design_reference/branding/logo/README.md`  
**Lead Designer:** Agent 02 (UI/UX Designer)

---

## 1. Brand Mark Overview

The NETRAVA brand mark is an organic, harmonious fusion of ophthalmic and botanical motifs, symbolizing clarity, health, and vision restoration.

```
       / \       / \
      /   \     /   \
     ( LEAF)   ( LEAF)
      \   /     \   /
       \ /       \ /
           \   /
            \ /
          NETRAVA
    SEE. DETECT. EXPLAIN.
    ─────────────────────
```

---

## 2. Emblem Anatomy

1. **Left Leaf Emblem (Primary Forest Green — `#075E4D` / `#005D49`):**
   - Represents medical authority, trust, and optical science.
   - Drawn using custom cubic bezier curves with an inner stylized vein painted in translucent mint (`#EAF7F1` at 60% opacity).
2. **Right Leaf Emblem (Secondary Vibrant Green — `#3C9A78` / `#149477`):**
   - Represents vitality, technological innovation, and patient well-being.
   - Symmetrically balanced with a right-leaning curve and matching inner vein.
3. **Brand Wordmark ("NETRAVA"):**
   - Font: Poppins Bold / ExtraBold (800).
   - Letter Spacing: +3.5px.
   - Color: `AppColors.primaryGreen` (`#075E4D`).
4. **Brand Tagline ("SEE. DETECT. EXPLAIN."):**
   - Font: Poppins SemiBold (600).
   - Letter Spacing: +4.2px.
   - Size: 10.5px.
   - Color: `AppColors.primaryGreen` (`#075E4D`).
5. **Horizontal Accent Bar:**
   - Width: 32px, Height: 3px, Radius: 2px.
   - Color: `AppColors.secondaryGreen` (`#3C9A78`).

---

## 3. Flutter Implementation

The logo is implemented natively as a custom vector painter in:
`frontend/flutter_app/lib/features/welcome/widgets/netrava_logo.dart`

It accepts a `size` scaling multiplier to render crisply at any resolution without bitmap pixelation.

