# NETRAVA — AI Model Registry & Inference Pipeline

**Backbone:** EfficientNet-B3 (`timm.create_model('efficientnet_b3', pretrained=False, num_classes=5, drop_rate=0.30)`)  
**Resolution:** 300 $\times$ 300 pixels (LANCZOS Aspect-ratio preserved with black padding)  
**Lead Engineer:** Agent 04 (AI/ML Integration Engineer)

---

## 1. Directory Structure

```
ai_model/
├── checkpoint/              # Model weight binaries (.pth)
│   └── best_efficientnet_b3_staged.pth
├── inference/               # Production inference engine
│   ├── __init__.py          # Public package API
│   ├── model_loader.py      # Architecture reconstruction & safe weight loader
│   ├── preprocessing.py     # Aspect-ratio preserving 300x300 padding & normalization
│   ├── gradcam.py           # Grad-CAM explainability hooked to conv_head
│   ├── predictor.py         # End-to-end 5-class prediction orchestrator
│   └── schemas.py           # Pydantic V2 input/output schemas
├── tests/                   # Automated pytest suite
│   ├── test_model_loader.py
│   ├── test_preprocessing.py
│   ├── test_prediction.py
│   └── test_gradcam.py
├── evaluation/              # QWK validation curves, confusion matrices
└── reference/               # Training Jupyter notebooks
    └── NETRAVA_B3_Improved_Training.ipynb
```

---

## 2. Checkpoint Details & Validation

- **File Name:** `best_efficientnet_b3_staged.pth`
- **Output Classes:** 5 (0: No DR, 1: Mild, 2: Moderate, 3: Severe, 4: Proliferative DR)
- **Validation QWK:** 0.8716 (Quadratic Weighted Kappa)
- **Loss Function:** `CrossEntropyLoss` with square-root class frequency weighting and 0.02 label smoothing
- **Grad-CAM Target Layer:** `model.conv_head`

---

## 3. Quickstart: Running Inference & Explainability

```python
from ai_model.inference import NetravaPredictor

# Initialize predictor on CPU or CUDA
predictor = NetravaPredictor()

# Run prediction with Grad-CAM heatmap
result = predictor.predict(
    "path/to/fundus_scan.png",
    return_gradcam=True,
    save_overlay_path="output_heatmap.png"
)

print(f"Predicted Grade: {result.predicted_grade} ({result.severity_label})")
print(f"Confidence: {result.confidence_score * 100:.2f}%")
print(f"Referral Needed: {result.is_referral_recommended}")
print(f"Inference Latency: {result.inference_time_ms} ms")
```

---

## 4. Running Automated Tests

```bash
python -m pytest ai_model/tests/ -v
```
