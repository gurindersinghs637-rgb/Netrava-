"""
NETRAVA — Screening Service
=============================
Handles retinal image upload, QC assessment, and Supabase Storage persistence.

Image QC uses a Laplacian variance blur filter (higher score = sharper image).
Gradable threshold: blur_score ≥ 50.0 (configurable).

Design:
- Receives pre-validated PIL Image from backend.app.ml.image_validator.
- Runs QC on the image.
- Stores the fundus image in Supabase Storage (private bucket).
- Inserts a retinal_images row in the database.
- Returns a 30-minute signed URL for the stored fundus image.
"""

from __future__ import annotations

import asyncio
import io
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np
from fastapi import HTTPException, status
from loguru import logger
from PIL import Image

from backend.app.core.config import settings
from backend.app.services.database_errors import raise_known_database_error
from backend.app.schemas.screening import CreateScreeningResponse, QCAssessment

_QC_BLUR_THRESHOLD = 50.0
_QC_BUCKET = "fundus-images"


def _compute_blur_score(image: Image.Image) -> float:
    """Compute Laplacian variance as a sharpness metric.

    Higher values indicate sharper images.
    A score below _QC_BLUR_THRESHOLD is considered ungradable.
    """
    import cv2  # type: ignore

    gray = np.array(image.convert("L"))
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return round(laplacian_var, 2)


def _assess_qc(image: Image.Image) -> QCAssessment:
    """Run image quality control checks."""
    blur_score = _compute_blur_score(image)
    is_gradable = blur_score >= _QC_BLUR_THRESHOLD

    # Simple illumination heuristic: mean pixel brightness
    arr = np.array(image.convert("RGB"))
    mean_brightness = float(arr.mean())
    if mean_brightness < 50:
        illumination = "underexposed"
    elif mean_brightness > 200:
        illumination = "overexposed"
    else:
        illumination = "optimal"

    # Combined confidence: high if both blur and illumination are good
    blur_conf = min(blur_score / 200.0, 1.0)
    illum_conf = 1.0 if illumination == "optimal" else 0.5
    confidence = round((blur_conf + illum_conf) / 2.0, 3)

    return QCAssessment(
        is_gradable=is_gradable,
        blur_score=blur_score,
        illumination=illumination,
        confidence=confidence,
    )


async def create_screening(
    patient_id: str,
    eye: str,
    image: Image.Image,
    raw_bytes: bytes,
    filename: str,
    technician_id: str,
    clinic_id: str,
) -> CreateScreeningResponse:
    """Upload a retinal image, run QC, and create a screening record.

    Args:
        patient_id: UUID of the patient being screened.
        eye: "OD" (right) or "OS" (left).
        image: Validated PIL Image.
        raw_bytes: Original file bytes for storage upload.
        filename: Original uploaded filename.
        technician_id: UUID of the field technician.

    Returns:
        CreateScreeningResponse with screening IDs, QC result, and signed URL.

    Raises:
        HTTPException 422: Image is ungradable.
        HTTPException 503: Storage unavailable.
    """
    # ── 1. Quality Control ────────────────────────────────────────────────────
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "SCREENING_UNAVAILABLE", "message": "Screening storage and database are not configured."},
        )
    try:
        from supabase import create_client  # type: ignore
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        patient = client.table("patients").select("id").eq("id", patient_id).eq("clinic_id", clinic_id).execute()
        if not patient.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "PATIENT_NOT_FOUND", "message": "Patient was not found in this clinic."})
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Patient clinic verification failed: {}", type(exc).__name__)
        raise_known_database_error(exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"error": "DATABASE_ERROR", "message": "Patient access could not be verified."}) from exc

    qc = _assess_qc(image)
    if not qc.is_gradable:
        logger.warning(
            "Ungradable image: eye={}, blur_score={}",
            eye, qc.blur_score,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "IMAGE_UNGRADABLE",
                "message": (
                    f"The retinal image is too blurry for diagnosis "
                    f"(blur score: {qc.blur_score}, required ≥ {_QC_BLUR_THRESHOLD}). "
                    "Please recapture the image."
                ),
                "qc": qc.model_dump(),
            },
        )

    # ── 2. Generate UUIDs ─────────────────────────────────────────────────────
    screening_id = str(uuid.uuid4())
    retinal_image_id = str(uuid.uuid4())

    # ── 3. Upload fundus image to Supabase Storage ────────────────────────────
    image_suffix = "png" if raw_bytes.startswith(b"\x89PNG\r\n\x1a\n") else "jpg"
    signed_url = await _upload_fundus_image(
        raw_bytes=raw_bytes,
        retinal_image_id=retinal_image_id,
        clinic_id=clinic_id,
        image_format="PNG" if image_suffix == "png" else "JPEG",
    )

    # ── 4. Persist records to database ────────────────────────────────────────
    try:
        await _save_screening_records(
            screening_id=screening_id,
            retinal_image_id=retinal_image_id,
            patient_id=patient_id,
            eye=eye,
            technician_id=technician_id,
            clinic_id=clinic_id,
            qc=qc,
            storage_path=f"{clinic_id}/{retinal_image_id}.{image_suffix}",
            file_size_bytes=len(raw_bytes),
            image_width=image.width,
            image_height=image.height,
            content_sha256=hashlib.sha256(raw_bytes).hexdigest(),
        )
    except Exception as exc:
        await _delete_screening_record(screening_id, clinic_id)
        await _delete_fundus_image(retinal_image_id, clinic_id)
        raise_known_database_error(exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "SCREENING_PERSISTENCE_FAILED", "message": "Screening could not be saved."},
        ) from exc

    logger.info(
        "Screening created: eye={}, blur={}",
        eye, qc.blur_score,
    )

    return CreateScreeningResponse(
        screening_id=screening_id,
        retinal_image_id=retinal_image_id,
        eye=eye,  # type: ignore[arg-type]
        qc_assessment=qc,
        fundus_image_signed_url=signed_url,
        created_at=datetime.now(tz=timezone.utc),
    )


async def _upload_fundus_image(raw_bytes: bytes, retinal_image_id: str, clinic_id: str, image_format: str) -> str:
    """Upload raw fundus image bytes to Supabase Storage and return a signed URL."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "STORAGE_UNAVAILABLE", "message": "Medical image storage is not configured."},
        )

    try:
        from supabase import create_client  # type: ignore

        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        suffix = "png" if image_format.upper() == "PNG" else "jpg"
        content_type = "image/png" if suffix == "png" else "image/jpeg"
        storage_path = f"{clinic_id}/{retinal_image_id}.{suffix}"

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: client.storage.from_(_QC_BUCKET).upload(
                storage_path, raw_bytes, {"content-type": content_type, "upsert": "true"}
            ),
        )

        # 30-minute signed URL
        signed = client.storage.from_(_QC_BUCKET).create_signed_url(
            storage_path, expires_in=1800
        )
        signed_url = signed.get("signedURL")
        if not signed_url:
            raise RuntimeError("Storage provider did not return a signed URL.")
        return signed_url

    except Exception as exc:
        logger.error("Fundus upload failed: {}", type(exc).__name__)
        await _delete_fundus_image(retinal_image_id, clinic_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "STORAGE_ERROR", "message": "Could not upload retinal image."},
        ) from exc


async def _save_screening_records(
    screening_id: str,
    retinal_image_id: str,
    patient_id: str,
    eye: str,
    technician_id: str,
    clinic_id: str,
    qc: QCAssessment,
    storage_path: str,
    file_size_bytes: int | None = None,
    image_width: int | None = None,
    image_height: int | None = None,
    content_sha256: str | None = None,
) -> None:
    """Insert screening and retinal_image rows into the database."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Supabase database is not configured.")

    try:
        from supabase import create_client  # type: ignore

        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

        result = client.rpc(
            "create_screening_records",
            {
                "p_screening": {
                    "id": screening_id,
                    "clinic_id": clinic_id,
                    "patient_id": patient_id,
                    "technician_id": technician_id,
                },
                "p_image": {
                    "id": retinal_image_id,
                    "eye": eye,
                    "storage_path": storage_path,
                    "is_gradable": qc.is_gradable,
                    "blur_score": qc.blur_score,
                    "illumination": qc.illumination,
                    "qc_confidence": qc.confidence,
                    "mime_type": "image/png" if storage_path.endswith(".png") else "image/jpeg",
                    "file_size_bytes": file_size_bytes,
                    "image_width": image_width,
                    "image_height": image_height,
                    "content_sha256": content_sha256,
                },
            },
        ).execute()
        if not result.data:
            raise RuntimeError("Screening records RPC returned no confirmation.")

    except Exception as exc:
        logger.error("Screening record save failed: {}", type(exc).__name__)
        raise


async def _delete_fundus_image(retinal_image_id: str, clinic_id: str) -> None:
    """Best-effort compensation when database persistence fails after upload."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return
    try:
        from supabase import create_client  # type: ignore
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        await asyncio.get_running_loop().run_in_executor(
            None,
            lambda: client.storage.from_(_QC_BUCKET).remove([f"{clinic_id}/{retinal_image_id}.jpg", f"{clinic_id}/{retinal_image_id}.png"]),
        )
    except Exception as exc:
        logger.error("Compensating image deletion failed: {}", type(exc).__name__)


async def _delete_screening_record(screening_id: str, clinic_id: str) -> None:
    """Best-effort rollback of partial screening rows after a failed insert."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return
    try:
        from supabase import create_client  # type: ignore
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        await asyncio.get_running_loop().run_in_executor(
            None,
            lambda: client.table("screenings").delete().eq("id", screening_id).eq("clinic_id", clinic_id).execute(),
        )
    except Exception as exc:
        logger.error("Compensating screening-row deletion failed: {}", type(exc).__name__)

