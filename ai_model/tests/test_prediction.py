"""Automated tests for NetravaPredictor and 5-class severity inference."""

from pathlib import Path
import pytest
from PIL import Image

from ai_model.inference.model_loader import DEFAULT_CHECKPOINT_PATH
from ai_model.inference.predictor import NetravaPredictor
from ai_model.inference.schemas import CLASS_NAMES, PredictionResult

SAMPLE_IMAGE_PATH = Path(__file__).resolve().parent / "data" / "000c1434d8d7.png"


@pytest.fixture(scope="module")
def predictor() -> NetravaPredictor:
    """Shared predictor instance loaded onto CPU."""
    return NetravaPredictor(checkpoint_path=DEFAULT_CHECKPOINT_PATH, device="cpu")


class TestPredictor:
    """Test suite verifying end-to-end inference, probability calculation, and timings."""

    def test_predict_real_fundus_image(self, predictor: NetravaPredictor) -> None:
        """Verify inference on actual retinal fundus image returns valid PredictionResult."""
        if not SAMPLE_IMAGE_PATH.exists():
            pytest.skip(f"Sample test image not found at: {SAMPLE_IMAGE_PATH}")

        result = predictor.predict(
            SAMPLE_IMAGE_PATH,
            return_gradcam=True,
        )

        assert isinstance(result, PredictionResult)
        assert 0 <= result.predicted_grade <= 4
        assert result.severity_label == CLASS_NAMES[result.predicted_grade]
        assert 0.0 <= result.confidence_score <= 1.0
        assert len(result.probabilities) == 5
        assert len(result.raw_logits) == 5

        # Probabilities must sum to 1.0
        prob_sum = sum(p.probability for p in result.probabilities)
        assert pytest.approx(prob_sum, abs=1e-3) == 1.0

        # Latency check
        assert result.inference_time_ms > 0

        # Clinical recommendation check
        assert len(result.clinical_recommendation) > 10

        # Grad-CAM explanation check
        assert result.explanation is not None
        assert result.explanation.target_layer == "conv_head"
        assert result.explanation.heatmap_base64 is not None

    def test_predict_without_gradcam(self, predictor: NetravaPredictor) -> None:
        """Verify inference can skip Grad-CAM generation for lower latency."""
        dummy_img = Image.new("RGB", (300, 300), color=(120, 50, 30))
        result = predictor.predict(dummy_img, return_gradcam=False)

        assert result.explanation is None
        assert result.confidence_score > 0

    def test_referral_threshold_logic(self, predictor: NetravaPredictor) -> None:
        """Verify referral recommendation flag triggers for Moderate, Severe, or PDR."""
        dummy_img = Image.new("RGB", (300, 300), color=(120, 50, 30))
        result = predictor.predict(dummy_img, return_gradcam=False)

        if result.predicted_grade >= 2:
            assert result.is_referral_recommended is True
        else:
            assert result.is_referral_recommended is False

    def test_save_overlay_path(self, predictor: NetravaPredictor, tmp_path: Path) -> None:
        """Verify saving the blended heatmap overlay image to disk."""
        overlay_dest = tmp_path / "test_overlay.png"
        dummy_img = Image.new("RGB", (300, 300), color=(100, 40, 20))

        result = predictor.predict(
            dummy_img,
            return_gradcam=True,
            save_overlay_path=overlay_dest,
        )

        assert overlay_dest.exists()
        assert overlay_dest.stat().st_size > 0
        assert result.explanation is not None
        assert result.explanation.overlay_saved_path == str(overlay_dest.resolve())
