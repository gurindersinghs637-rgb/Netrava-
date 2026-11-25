"""
NETRAVA — Prediction Service
==============================
Orchestrates AI inference, Grad-CAM, and prediction persistence.

Design:
- Calls ai_model.inference via app.ml.model_bridge (never duplicates ML code).
- Acquires the Grad-CAM lock before backward pass.
- Stores results and Grad-CAM overlay in Supabase Storage.
- Returns signed URLs (30-minute expiry) — never permanent URLs.
- Referral is recommended for Grade ≥ 2 (Moderate DR).
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Any, Optional, Tuple

from fastapi import HTTPException, status
from loguru import logger
from PIL import Image

from backend.app.core.config import settings
from backend.app.services.database_errors import raise_known_database_error
from backend.app.ml.model_bridge import get_gradcam_lock, get_predictor
from backend.app.schemas.screening import (
    ClassProbabilityResponse,
    GradCAMExplanation,
    PredictResponse,
)

# DR grade labels (must match training class order)
_GRADE_LABELS = ["No DR", "Mild", "Moderate", "Severe", "Proliferative DR"]

# Referral threshold — Grade ≥ 2 requires ophthalmologist review
_REFERRAL_THRESHOLD = 2


def _get_storage_client() -> Any:
    """Return a Supabase client for storage operations."""
    from supabase import create_client  # type: ignore
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def _verify_image_in_clinic(client: Any, retinal_image_id: str, clinic_id: str, raw_bytes: bytes | None = None) -> None:
    """Verify an image through its live screening relationship and fail closed."""
    image_record = (
        client.table("retinal_images")
        .select("id,content_sha256,screenings!inner(clinic_id)")
        .eq("id", retinal_image_id)
        .eq("screenings.clinic_id", clinic_id)
        .execute()
    )
    if not image_record.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "IMAGE_NOT_FOUND", "message": "Image was not found in this clinic."},
        )
    if raw_bytes is not None:
        digest = image_record.data[0].get("content_sha256")
        if not digest:
            raise HTTPException(status_code=409, detail={"error": "IMAGE_REUPLOAD_REQUIRED", "message": "Create a new screening upload before analyzing this historical image."})
        if digest != hashlib.sha256(raw_bytes).hexdigest():
            raise HTTPException(status_code=422, detail={"error": "IMAGE_MISMATCH", "message": "Prediction upload must match the original screening image."})


async def run_prediction(
    retinal_image_id: str,
    image: Image.Image,
    raw_bytes: bytes,
    requested_by: str,
    clinic_id: str,
) -> PredictResponse:
    """Run AI inference and Grad-CAM on a validated retinal image.

    Args:
        retinal_image_id: UUID of the stored retinal image record.
        image: PIL Image (RGB, already validated).
        raw_bytes: Original file bytes (for storage upload if needed).
        requested_by: User ID of the requesting technician / ophthalmologist.

    Returns:
        PredictResponse with grades, probabilities, and Grad-CAM signed URL.

    Raises:
        HTTPException 503: Model not loaded.
        HTTPException 500: Inference error.
    """
    if not settings.is_testing:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "DATABASE_UNAVAILABLE", "message": "Prediction requires a configured clinic database."},
            )
        try:
            from supabase import create_client  # type: ignore
            client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
            _verify_image_in_clinic(client, retinal_image_id, clinic_id, raw_bytes)
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Prediction image access check failed: {}", type(exc).__name__)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "DATABASE_ERROR", "message": "Image clinic access could not be verified."},
            ) from exc

    try:
        predictor = get_predictor()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "MODEL_NOT_LOADED", "message": "AI model is not available."},
        ) from exc

    # ── Run inference with Grad-CAM lock ─────────────────────────────────────
    gradcam_lock = get_gradcam_lock()
    async with gradcam_lock:
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: predictor.predict(image, return_gradcam=True),  # type: ignore[attr-defined]
            )
        except Exception as exc:
            logger.error("Inference failed: {}", type(exc).__name__)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "INFERENCE_ERROR", "message": "AI inference failed."},
            ) from exc

    predicted_grade: int = result.predicted_grade  # type: ignore[attr-defined]
    confidence: float = result.confidence_score  # type: ignore[attr-defined]
    inference_ms: float = result.inference_time_ms  # type: ignore[attr-defined]
    probabilities = result.probabilities  # type: ignore[attr-defined]
    explanation = getattr(result, "explanation", None)
    heatmap_base64: Optional[str] = getattr(explanation, "heatmap_base64", None)
    gradcam_bytes = _decode_gradcam(heatmap_base64)

    logger.info(
        "Inference complete: grade={}, confidence={:.3f}, time={:.1f}ms",
        predicted_grade,
        confidence,
        inference_ms,
    )

    # ── Upload Grad-CAM heatmap to Supabase Storage ────────────────────────
    heatmap_signed_url, heatmap_storage_path = await _upload_gradcam(
        gradcam_bytes=gradcam_bytes,
        retinal_image_id=retinal_image_id,
        clinic_id=clinic_id,
    )

    # ── Persist prediction record ──────────────────────────────────────────
    try:
        prediction_id = await _save_prediction(
            retinal_image_id=retinal_image_id,
            predicted_grade=predicted_grade,
            confidence=confidence,
            inference_ms=inference_ms,
            probabilities=[item.probability for item in probabilities],
            requested_by=requested_by,
            clinic_id=clinic_id,
            heatmap_path=heatmap_storage_path,
        )
    except HTTPException:
        if heatmap_storage_path:
            await _delete_gradcam(heatmap_storage_path)
        raise

    prob_responses = [
        ClassProbabilityResponse(
            grade=i,
            class_name=_GRADE_LABELS[i],
            probability=float(p.probability),
        )
        for i, p in enumerate(probabilities)
    ]

    return PredictResponse(
        prediction_id=prediction_id,
        retinal_image_id=retinal_image_id,
        predicted_grade=predicted_grade,
        severity_label=_GRADE_LABELS[predicted_grade],
        confidence_score=round(confidence, 4),
        is_referral_recommended=predicted_grade >= _REFERRAL_THRESHOLD,
        probabilities=prob_responses,
        explanation=GradCAMExplanation(
            target_layer="conv_head",
            heatmap_signed_url=heatmap_signed_url,
            heatmap_base64=heatmap_base64,
        ),
        inference_time_ms=round(inference_ms, 2),
        persistence_status="persisted" if prediction_id else "not_configured",
    )


def _decode_gradcam(encoded: Optional[str]) -> Optional[bytes]:
    """Decode a predictor PNG overlay, rejecting malformed base64 data."""
    if encoded is None:
        return None
    try:
        return base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "INVALID_HEATMAP", "message": "AI explanation image could not be decoded."},
        ) from exc


async def _upload_gradcam(
    gradcam_bytes: Optional[bytes],
    retinal_image_id: str,
    clinic_id: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Upload a Grad-CAM overlay PNG to Supabase Storage and return a signed URL."""
    if gradcam_bytes is None or not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return None, None
    storage_path = f"{clinic_id}/{retinal_image_id}/{uuid.uuid4()}.png"
    try:
        from supabase import create_client  # type: ignore
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: client.storage.from_("gradcam-heatmaps").upload(
                storage_path, gradcam_bytes, {"content-type": "image/png", "upsert": "true"}
            ),
        )
        signed = client.storage.from_("gradcam-heatmaps").create_signed_url(
            storage_path, expires_in=1800
        )
        signed_url = signed.get("signedURL")
        if not signed_url:
            raise RuntimeError("Storage provider did not return a signed heatmap URL.")
        return signed_url, storage_path
    except Exception as exc:
        await _delete_gradcam(storage_path)
        logger.error("Grad-CAM upload failed: {}", type(exc).__name__)
        raise HTTPException(status_code=503, detail={"error": "EXPLANATION_STORAGE_FAILED", "message": "AI explanation could not be stored."}) from exc


async def _delete_gradcam(storage_path: str) -> None:
    """Best-effort cleanup when prediction persistence fails after upload."""
    try:
        from supabase import create_client  # type: ignore
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        await asyncio.get_running_loop().run_in_executor(
            None,
            lambda: client.storage.from_("gradcam-heatmaps").remove([storage_path]),
        )
    except Exception as exc:
        logger.error("Compensating heatmap deletion failed: {}", type(exc).__name__)


async def _save_prediction(
    retinal_image_id: str,
    predicted_grade: int,
    confidence: float,
    inference_ms: float,
    probabilities: Any,
    requested_by: str,
    clinic_id: str,
    heatmap_path: Optional[str],
) -> Optional[str]:
    """Persist a prediction record to the database and return its UUID."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return None

    try:
        from supabase import create_client  # type: ignore

        payload = {
            "retinal_image_id": retinal_image_id,
            "clinic_id": clinic_id,
            "predicted_grade": predicted_grade,
            "severity_label": _GRADE_LABELS[predicted_grade],
            "confidence_score": round(confidence, 6),
            "inference_time_ms": round(inference_ms, 2),
            "probabilities": list(map(float, probabilities)),
            "gradcam_heatmap_path": heatmap_path,
            "is_referral_recommended": predicted_grade >= _REFERRAL_THRESHOLD,
            "requested_by": requested_by,
        }
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        result = client.rpc(
            "write_screening_prediction", {"p_prediction": payload}
        ).execute()
        row = result.data
        if isinstance(row, list):
            row = row[0] if row else None
        if not row:
            raise RuntimeError("Prediction insert returned no row.")
        return row["id"]

    except Exception as exc:
        logger.error("Prediction save failed: {}", type(exc).__name__)
        raise_known_database_error(exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "PREDICTION_PERSISTENCE_FAILED", "message": "Prediction could not be saved."},
        ) from exc

