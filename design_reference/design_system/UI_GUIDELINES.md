# NETRAVA Design System — Clinical UI/UX Guidelines

**Design System:** Clinical Precision AI  
**Document Version:** 1.0.0  
**Specification File:** `design_reference/design_system/UI_GUIDELINES.md`

---

## 1. Clinical Ergonomics in Point-of-Care Environments

Field technicians operating handheld ophthalmic cameras face unique ergonomic challenges:
1. **One-Handed Operation:** Technicians often stabilize a portable fundus lens with one hand while holding the smartphone with the other. Key actions (Capture, Retake, Run AI) must remain within the primary thumb zone (lower 35% of the viewport).
2. **Ambient Lighting Variations:** Field screenings occur in dimly lit examination rooms or sunlit rural outreach tents. The `#F5FAF7` pale canvas prevents retinal bleaching, while high-contrast text (`#081F1B`) ensures legibility under direct glare.
3. **Cognitive Load Minimization:** Clinicians review dozens of scans per hour. Avoid decorative clutter, animated splash distractions, or ambiguous iconography. Present diagnostic predictions with clear visual hierarchy.

---

## 2. Medical Safety & Disclaimer Enforcement

> [!IMPORTANT]
> **Regulatory and Clinical Mandate:**  
> AI predictions must **never** be presented as an autonomous final diagnosis.

Every screen and exported document displaying an AI prediction must include:
1. **Prominent Clinical Disclaimer:**
   > *"NETRAVA is an AI-assisted screening tool. Results are intended to aid clinical evaluation and must be validated by a certified ophthalmologist."*
2. **Confidence Metric Display:** Always pair severity classifications with the model's confidence percentage (e.g., `Moderate NPDR (Confidence: 94.2%)`).
3. **Grad-CAM Interpretation Warning:** Explicitly state below heatmaps:
   > *"Visual heatmaps indicate regions that influenced the AI prediction. They do not substitute for comprehensive fundoscopic examination."*

---

## 3. Offline Mode & Network Resilience

In rural screening camps where internet access may be intermittent:
- **Offline Banner:** Display an unobtrusive amber indicator (`#FEF6EB` / `#8A5200`) when connectivity is lost: *"Offline Mode: Screenings will be queued and synchronized upon reconnection."*
- **Local Storage:** Patient intake forms and captured fundus scans must be securely encrypted and persisted locally using SQLite / Hive before network transmission.
- **Sync Status Badges:** Display a `Sync Pending` chip on patient screening cards until the FastAPI server acknowledges receipt.

---

## 4. Optical Quality Control (QC) Gate

Never permit an ungradable scan to proceed to AI inference:
- If a captured image exhibits severe blur ($\sigma^2 < \text{threshold}$) or poor pupil illumination, block the "Run AI Analysis" CTA.
- Display a dedicated QC card with actionable guidance:
  - *"Image appears blurry. Ensure pupil alignment and steady lens focus before capturing."*
  - *"Severe underexposure detected. Increase fundus illumination or ensure adequate dark adaptation."*
- Provide a high-contrast **Retake Scan** primary button.

