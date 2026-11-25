"""Prepare the fixed retinal verification fixture and run production preflight.

Only the bundled fixture is resized, once to a documented 400-pixel bounding box.
Custom files are never transformed. No noise, sharpening or QC override is used.
"""
from __future__ import annotations

import io
from pathlib import Path

from fastapi import UploadFile
from PIL import Image

from backend.app.ml.image_validator import validate_and_load_image
from backend.app.schemas.screening import QCAssessment
from backend.app.services.screening_service import _assess_qc

SOURCE = Path(__file__).resolve().parents[2] / "ai_model/tests/data/001639a390f0.png"
FIXTURE_SIZE = 400


async def prepare_verification_image(path: Path | None = None) -> tuple[bytes, str, QCAssessment]:
    """Return validated upload bytes, MIME and QC before any live side effects."""
    if path is None:
        with Image.open(SOURCE) as source:
            image = source.convert("RGB")
            image.thumbnail((FIXTURE_SIZE, FIXTURE_SIZE), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            raw = buffer.getvalue()
    else:
        # Bound local reads just as the API bounds uploads; custom images stay intact.
        from backend.app.core.config import settings
        with path.open("rb") as stream:
            raw = stream.read(settings.MAX_IMAGE_SIZE_BYTES + 1)
    image, raw = await validate_and_load_image(UploadFile(filename="verification-image", file=io.BytesIO(raw)))
    qc = _assess_qc(image)
    if not qc.is_gradable:
        raise ValueError(f"Verification image failed production QC (blur_score={qc.blur_score}). Select a gradable image; no records were created.")
    return raw, "image/png" if raw.startswith(b"\x89PNG") else "image/jpeg", qc
