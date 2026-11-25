# Agent 04: AI/ML Integration Engineer

**Role Title:** Lead AI/ML Integration Engineer & Computer Vision Specialist  
**Agent Identifier:** `AGENT_04`  
**Instruction File:** `docs/agents/AGENT_04_AI_ML.md`  
**Governing Standard:** `AGENT.md` & `IMPLEMENTATION_PLAN.md`

---

## 1. Role Purpose & Mandate

Agent 04 is the custodian of the **NETRAVA Deep Learning Vision Engine**. Agent 04 is responsible for reconstructing the trained EfficientNet-B3 neural network, reproducing the exact training-time preprocessing pipeline, loading the saved checkpoint (`best_efficientnet_b3_staged.pth`), executing fast inference, and computing high-resolution **Grad-CAM** visual explanations from the network's convolutional head.

---

## 2. Work History & Status Report

- **Assigned Responsibility:** Phase 1 — AI Model Integration (Model Loader, Image Preprocessing, Prediction Engine, Grad-CAM, and Automated Tests).
- **Current Status:** `COMPLETED`
- **Date:** November 2, 2026

### Implementation Completed
1. **Model Loader (`ai_model/inference/model_loader.py`):**
   - Implemented `ModelLoader` class and `get_model()` singleton accessor.
   - Reconstructed exact trained architecture: `timm.create_model('efficientnet_b3', pretrained=False, num_classes=5, drop_rate=0.30)`.
   - Safely loads `best_efficientnet_b3_staged.pth` with `strict=True` (all 574 tensor keys matched successfully).
   - Validates model output dimensions $(1, 5)$ and sets `eval()` mode.
   - Robust error handling: `CheckpointNotFoundError` and `ModelLoadError`.
   - Auto-detects compute device (`cuda` or `cpu`).

2. **Image Preprocessing (`ai_model/inference/preprocessing.py`):**
   - Implemented `ResizeWithPadding(size=300, fill=(0, 0, 0))` using LANCZOS interpolation, preserving aspect ratio.
   - Implemented ImageNet channel normalization ($\mu = [0.485, 0.456, 0.406]$, $\sigma = [0.229, 0.224, 0.225]$).
   - Preprocessor accepts file paths, raw bytes, binary streams, and PIL Image instances.
   - Returns both normalized PyTorch tensor $(1, 3, 300, 300)$ and padded display image $(300 \times 300)$.
   - Validates input formats and rejects corrupt/empty payloads (`ImageValidationError`).

3. **Grad-CAM Explainability (`ai_model/inference/gradcam.py`):**
   - Targets the documented `model.conv_head` layer.
   - Registers forward and full backward hooks, backpropagating on top predicted class or target class.
   - Computes gradient-weighted channel activations with ReLU rectification and bilinear interpolation to $300 \times 300$.
   - Normalizes heatmap to $[0.0, 1.0]$ and blends with display image using Jet colormap ($\alpha = 0.40$).
   - Safely unregisters hooks in a `finally:` block, preventing memory leaks.
   - Provides `to_base64()` serialization for API delivery.

4. **Prediction Engine (`ai_model/inference/predictor.py`):**
   - Implemented `NetravaPredictor` orchestrating preprocessing, model forward pass, Softmax probabilities, and Grad-CAM.
   - Computes predicted grade (0–4), confidence score, referral recommendation (`grade >= 2`), clinical action guidance, and execution latency.
   - Supports optional overlay persistence to disk.

5. **Pydantic Schemas (`ai_model/inference/schemas.py`):**
   - Formulated `ClassProbability`, `GradCAMResult`, and `PredictionResult` adhering to OpenAPI contracts.

### Files Created or Modified
- `ai_model/inference/__init__.py`
- `ai_model/inference/schemas.py`
- `ai_model/inference/model_loader.py`
- `ai_model/inference/preprocessing.py`
- `ai_model/inference/gradcam.py`
- `ai_model/inference/predictor.py`
- `ai_model/tests/test_model_loader.py`
- `ai_model/tests/test_preprocessing.py`
- `ai_model/tests/test_prediction.py`
- `ai_model/tests/test_gradcam.py`
- `ai_model/tests/data/000c1434d8d7.png` (Sample retinal test image)
- `ai_model/tests/data/001639a390f0.png` (Sample retinal test image)
- `ai_model/README.md` (Updated with usage and test guide)

### Tests Executed & Results
- **Test Framework:** Pytest 9.2.0 on Python 3.11 (`C:\Users\HP\.conda\envs\py311\python.exe`).
- **Command:** `python -m pytest ai_model/tests/ -v`
- **Result:** **20 passed in 14.38s (100% PASS RATE)**.
  - `test_default_checkpoint_exists`: PASSED
  - `test_load_trained_model_successfully`: PASSED
  - `test_checkpoint_metadata_extracted`: PASSED (epoch: 20, best_val_qwk: 0.8716)
  - `test_model_output_dimensions`: PASSED (shape: [1, 5])
  - `test_invalid_checkpoint_path_raises_error`: PASSED
  - `test_singleton_get_model_accessor`: PASSED
  - `test_resize_with_padding_wide_image`: PASSED (aspect ratio preserved, black borders)
  - `test_resize_with_padding_tall_image`: PASSED (aspect ratio preserved, black borders)
  - `test_preprocess_from_file_path`: PASSED (shape: [1, 3, 300, 300])
  - `test_preprocess_from_raw_bytes`: PASSED
  - `test_preprocess_from_pil_image`: PASSED
  - `test_invalid_image_raises_validation_error`: PASSED
  - `test_predict_real_fundus_image`: PASSED (Valid PredictionResult, prob sum = 1.0)
  - `test_predict_without_gradcam`: PASSED
  - `test_referral_threshold_logic`: PASSED
  - `test_save_overlay_path`: PASSED
  - `test_gradcam_initialization_with_conv_head`: PASSED
  - `test_gradcam_heatmap_dimensions_and_normalization`: PASSED (shape: [300, 300], range [0, 1])
  - `test_hooks_are_cleaned_up_without_leakage`: PASSED (0 hook leakage)
  - `test_base64_serialization`: PASSED

- **Real Inference Benchmark:**
  - Input: `ai_model/tests/data/000c1434d8d7.png`
  - Output: Grade 2 (Moderate NPDR), Confidence: 84.10%, Referral: True
  - Latency: 95.1 ms on CPU.

### Known Issues
- None. All 20 tests pass without failures or warnings.

### Decisions & Dependencies
- Checkpoint `best_efficientnet_b3_staged.pth` confirmed intact and verified with strict weight matching.
- Grad-CAM layer confirmed as `model.conv_head`.
- Handover to Backend Engineer (Agent 02 / Agent 03) is ready: the `NetravaPredictor` module can now be directly imported into FastAPI routes (`backend/app/api/v1/predict.py`).

### Recommended Next Task
Proceed with **Phase 2 (Supabase Database)** and **Phase 3 (FastAPI Backend)** integration, using `ai_model.inference.NetravaPredictor` as the prediction engine.
