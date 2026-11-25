"""Automated tests for Grad-CAM explainability and hook management."""

from pathlib import Path
import numpy as np
import pytest
import torch
from PIL import Image

from ai_model.inference.gradcam import GradCAM
from ai_model.inference.model_loader import DEFAULT_CHECKPOINT_PATH, ModelLoader
from ai_model.inference.preprocessing import ImagePreprocessor

SAMPLE_IMAGE_PATH = Path(__file__).resolve().parent / "data" / "000c1434d8d7.png"


@pytest.fixture(scope="module")
def model_and_preprocessor():
    """Loads model and preprocessor on CPU."""
    loader = ModelLoader(checkpoint_path=DEFAULT_CHECKPOINT_PATH, device="cpu")
    model = loader.load()
    preprocessor = ImagePreprocessor(img_size=300)
    return model, preprocessor


class TestGradCAM:
    """Test suite verifying Grad-CAM hook management, heatmaps, and overlay blending."""

    def test_gradcam_initialization_with_conv_head(self, model_and_preprocessor) -> None:
        """Verify Grad-CAM correctly identifies and targets the conv_head module."""
        model, _ = model_and_preprocessor
        gradcam = GradCAM(model=model, layer_name="conv_head")
        assert gradcam.target_layer is not None
        assert hasattr(gradcam.target_layer, "weight")

    def test_gradcam_heatmap_dimensions_and_normalization(self, model_and_preprocessor) -> None:
        """Verify generated heatmap is (300, 300) normalized to [0.0, 1.0]."""
        model, preprocessor = model_and_preprocessor
        gradcam = GradCAM(model=model, layer_name="conv_head")

        if SAMPLE_IMAGE_PATH.exists():
            input_tensor, display_img = preprocessor.preprocess(SAMPLE_IMAGE_PATH)
        else:
            dummy_img = Image.new("RGB", (300, 300), color=(140, 60, 40))
            input_tensor, display_img = preprocessor.preprocess(dummy_img)

        cam_norm, overlay_img, min_val, max_val = gradcam.generate(
            input_tensor=input_tensor,
            display_image=display_img,
            target_class=2,  # Moderate DR
            alpha=0.40,
        )

        assert isinstance(cam_norm, np.ndarray)
        assert cam_norm.shape == (300, 300)
        assert cam_norm.min() >= 0.0
        assert cam_norm.max() <= 1.0
        assert isinstance(overlay_img, Image.Image)
        assert overlay_img.size == (300, 300)
        assert overlay_img.mode == "RGB"

    def test_hooks_are_cleaned_up_without_leakage(self, model_and_preprocessor) -> None:
        """Verify PyTorch hooks are removed in finally block, preventing memory leaks."""
        model, preprocessor = model_and_preprocessor
        gradcam = GradCAM(model=model, layer_name="conv_head")

        initial_forward_hooks = len(gradcam.target_layer._forward_hooks)
        initial_backward_hooks = len(gradcam.target_layer._backward_hooks)

        dummy_img = Image.new("RGB", (300, 300), color=(140, 60, 40))
        input_tensor, display_img = preprocessor.preprocess(dummy_img)

        gradcam.generate(input_tensor=input_tensor, display_image=display_img)

        # After execution, hook counts must be exactly back to initial state
        assert len(gradcam.target_layer._forward_hooks) == initial_forward_hooks
        assert len(gradcam.target_layer._backward_hooks) == initial_backward_hooks

    def test_base64_serialization(self) -> None:
        """Verify image encoding to base64 data string."""
        sample_img = Image.new("RGB", (50, 50), color=(255, 0, 0))
        b64_str = GradCAM.to_base64(sample_img)

        assert isinstance(b64_str, str)
        assert len(b64_str) > 100
