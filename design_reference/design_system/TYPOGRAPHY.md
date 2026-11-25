# NETRAVA Design System — Typography

**Design System:** Clinical Precision AI  
**Document Version:** 1.0.0  
**Specification File:** `design_reference/design_system/TYPOGRAPHY.md`

---

## 1. Primary Font Families

NETRAVA utilizes two primary font families optimized for mobile diagnostic clarity:

1. **Inter:** Primary interface typeface for UI controls, patient lists, body text, medical labels, and tabular numeric figures (`tnum`). Renowned for its tall x-height and exceptional legibility on high-DPI smartphone screens.
2. **Poppins:** Brand display typeface used for the main brand title ("NETRAVA"), landing screen headers, and prominent marketing milestones.

---

## 2. Typographic Scale & Styles Hierarchy

| Token Name | Font Family | Size (px) | Weight | Line Height | Letter Spacing | Semantic Usage |
|---|---|---|---|---|---|---|
| `brand-title` | Poppins | 32px | Bold (800) | 38px | +3.5px | Splash & Welcome brand headline ("NETRAVA"). |
| `brand-tagline` | Poppins | 10.5px | SemiBold (600) | 14px | +4.0px | Tagline ("SEE. DETECT. EXPLAIN."). |
| `headline-xl` | Inter | 32px | Bold (700) | 38px | -0.02em | Triage metrics and primary screen titles. |
| `headline-lg` | Inter | 26px | Bold (700) | 32px | -0.015em | Section titles, patient profile name headers. |
| `headline-md` | Inter | 20px | SemiBold (600) | 26px | -0.01em | Diagnostic card titles, ICDR severity headings. |
| `headline-sm` | Inter | 17px | SemiBold (600) | 22px | Normal | Subheadings, card titles, dialogue headers. |
| `body-lg` | Inter | 16px | Regular (400) | 24px | Normal | Primary body text, clinical recommendations. |
| `body-md` | Inter | 14px | Regular (400) | 20px | Normal | Standard body text, intake form field text. |
| `body-sm` | Inter | 13px | Regular (400) | 18px | Normal | Captions, helper text, medical disclaimers. |
| `label-lg` | Inter | 14px | SemiBold (600) | 18px | +0.01em | Primary button labels, active tab titles. |
| `label-md` | Inter | 12px | SemiBold (600) | 16px | +0.02em | Secondary button labels, input field labels. |
| `label-sm` | Inter | 11px | Bold (700) | 14px | +0.04em | Pill badge text, eye tags (OD / OS), status tags. |
| `mono-metric` | Inter / Monospace | 22px | Bold (700) | 26px | -0.02em | Confidence percentages (e.g., `94.8%`), HbA1c values. |

---

## 3. Tabular Figures & Numerical Rules

In clinical diagnostic apps, numbers must never shift horizontal alignment during live updates or table parsing:
- **Enable Tabular Figures:** Always use `fontFeatures: [FontFeature.tabularFigures()]` in Flutter for confidence scores, grading values, eye indicators, and timestamps.
- **Percentages:** Display confidence scores with exactly one decimal place (e.g., `96.4%`).
- **Retinal Scan Identifiers:** Display MRN and scan IDs in uppercase alphanumeric formatting with slight letter spacing (`MRN: 8934-21A`).

---

## 4. Flutter Text Styles Implementation Reference

```dart
// frontend/flutter_app/lib/core/theme/app_text_styles.dart
import 'dart:ui';
import 'package:flutter/material.dart';
import 'app_colors.dart';

class AppTextStyles {
  AppTextStyles._();

  static const TextStyle brandTitle = TextStyle(
    fontFamily: 'Poppins',
    fontSize: 32,
    fontWeight: FontWeight.w800,
    color: AppColors.primaryGreen,
    letterSpacing: 3.5,
  );

  static const TextStyle brandTagline = TextStyle(
    fontFamily: 'Poppins',
    fontSize: 10.5,
    fontWeight: FontWeight.w600,
    color: AppColors.primaryGreen,
    letterSpacing: 4.0,
  );

  static const TextStyle headlineLg = TextStyle(
    fontFamily: 'Inter',
    fontSize: 26,
    fontWeight: FontWeight.w700,
    color: AppColors.textPrimary,
    letterSpacing: -0.4,
  );

  static const TextStyle headlineMd = TextStyle(
    fontFamily: 'Inter',
    fontSize: 20,
    fontWeight: FontWeight.w600,
    color: AppColors.textPrimary,
    letterSpacing: -0.2,
  );

  static const TextStyle bodyMd = TextStyle(
    fontFamily: 'Inter',
    fontSize: 14,
    fontWeight: FontWeight.w400,
    color: AppColors.textSecondary,
    height: 1.4,
  );

  static const TextStyle labelSm = TextStyle(
    fontFamily: 'Inter',
    fontSize: 11,
    fontWeight: FontWeight.w700,
    letterSpacing: 0.5,
  );

  static const TextStyle monoMetric = TextStyle(
    fontFamily: 'Inter',
    fontSize: 22,
    fontWeight: FontWeight.w700,
    fontFeatures: [FontFeature.tabularFigures()],
    letterSpacing: -0.5,
  );
}
```

