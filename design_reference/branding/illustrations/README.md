# NETRAVA Branding — Ambient Illustrations & Vectors

**File:** `design_reference/branding/illustrations/README.md`  
**Lead Designer:** Agent 02 (UI/UX Designer)

---

## 1. Ambient Background Decorations

To avoid stark clinical emptiness while preserving medical minimalism, NETRAVA incorporates layered organic shapes:

### 1.1 Bottom Wave Painter (`NetravaBottomWaves`)
- **Location:** Pinned to the lower screen boundary on landing and authentication views.
- **Implementation:** Vector `CustomPainter` rendering four layered cubic bezier curves in descending green hues:
  - Deep Wave: `#075E4D` (`AppColors.waveDark`)
  - Mid Wave: `#23846C` (`AppColors.waveMedium`)
  - Light Wave: `#5EB395` (`AppColors.waveLight`)
  - Tint Wave: `#A5DEC8` (`AppColors.waveSoftTint`)
- **Code:** `frontend/flutter_app/lib/features/welcome/widgets/bottom_waves.dart`.

### 1.2 Radial Gradient Orbs (`BackgroundDecorations`)
- Translucent blurred circles (`BoxShape.circle`, 150–220px diameter) placed behind brand headlines to create depth.
- Color: `#075E4D` with 4% to 8% opacity.
- Code: `frontend/flutter_app/lib/features/welcome/widgets/background_decorations.dart`.

