"""API regression coverage for inference-result integration."""

from __future__ import annotations

import base64
import io
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from jose import jwt
from PIL import Image


def _auth_headers() -> dict[str, str]:
    token = jwt.encode(
        {"sub": "test-user", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "test-secret-key-for-pytest-only",
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def _png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), color=(80, 100, 120)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_predict_api_maps_model_result_and_gradcam(client, monkeypatch):
    """The API must map the real inference schema and explainability output."""
    from backend.app.services import prediction_service

    class FakePredictor:
        def predict(self, image, return_gradcam=True):
            assert image.mode == "RGB"
            assert return_gradcam is True
            return SimpleNamespace(
                predicted_grade=2,
                confidence_score=0.8,
                inference_time_ms=12.5,
                probabilities=[
                    SimpleNamespace(probability=value)
                    for value in (0.02, 0.03, 0.80, 0.10, 0.05)
                ],
                explanation=SimpleNamespace(
                    heatmap_base64=base64.b64encode(b"png-overlay").decode("ascii")
                ),
            )

    monkeypatch.setattr(prediction_service, "get_predictor", lambda: FakePredictor())
    response = client.post(
        "/api/v1/predict?retinal_image_id=00000000-0000-0000-0000-000000000001",
        headers=_auth_headers(),
        files={"image": ("fundus.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["predicted_grade"] == 2
    assert body["severity_label"] == "Moderate"
    assert len(body["probabilities"]) == 5
    assert abs(sum(item["probability"] for item in body["probabilities"]) - 1.0) < 1e-6
    assert body["is_referral_recommended"] is True  # Grade 2 is the referral threshold.
    assert body["explanation"]["target_layer"] == "conv_head"
    assert body["explanation"]["heatmap_base64"] == base64.b64encode(b"png-overlay").decode("ascii")
    assert body["persistence_status"] == "not_configured"
    assert body["prediction_id"] is None


def test_predict_api_runs_real_checkpoint_and_gradcam(client, monkeypatch):
    """A synthetic image completes inference with the real checkpoint and Grad-CAM."""
    from backend.app.core.config import settings
    from backend.app.services import prediction_service
    from ai_model.inference import NetravaPredictor

    predictor = NetravaPredictor(checkpoint_path=settings.resolved_model_checkpoint_path, device="cpu")
    monkeypatch.setattr(prediction_service, "get_predictor", lambda: predictor)
    response = client.post(
        "/api/v1/predict?retinal_image_id=00000000-0000-0000-0000-000000000002",
        headers=_auth_headers(),
        files={"image": ("synthetic-test.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert 0 <= body["predicted_grade"] <= 4
    assert len(body["probabilities"]) == 5
    assert abs(sum(item["probability"] for item in body["probabilities"]) - 1.0) < 1e-5
    assert body["explanation"]["target_layer"] == "conv_head"
    assert body["explanation"]["heatmap_base64"]
    assert body["persistence_status"] == "not_configured"
