"""
NETRAVA — ML Bridge: Image Validation
=======================================
Validates retinal fundus images at the API boundary according to
docs/SECURITY.md rules:
  - Magic byte check (JPEG / PNG only)
  - 15 MB file size cap
  - Pillow decompression bomb protection (MAX_IMAGE_PIXELS = 50_000_000)
  - Returns a PIL Image ready for the preprocessing pipeline
"""

from __future__ import annotations

import io
from typing import Tuple

from fastapi import HTTPException, UploadFile, status
from loguru import logger
from PIL import Image

from backend.app.core.config import settings

# Decompression bomb defence — must be set before any Image.open() call
Image.MAX_IMAGE_PIXELS = 50_000_000

# Magic bytes for supported formats
_MAGIC_JPEG = b"\xff\xd8\xff"
_MAGIC_PNG = b"\x89PNG\r\n\x1a\n"


async def validate_and_load_image(file: UploadFile) -> Tuple[Image.Image, bytes]:
    """Validate an uploaded image file and return a PIL Image.

    Checks performed (in order):
    1. File size ≤ 15 MB.
    2. Magic bytes match JPEG or PNG.
    3. Pillow can decode the image (catches corrupted files).
    4. Decompression bomb check via MAX_IMAGE_PIXELS.

    Args:
        file: FastAPI UploadFile from a multipart/form-data request.

    Returns:
        Tuple of (PIL.Image.Image in RGB mode, raw bytes).

    Raises:
        HTTPException 400: Invalid format or corrupted image.
        HTTPException 413: File exceeds 15 MB limit.
    """
    raw: bytes = await file.read(settings.MAX_IMAGE_SIZE_BYTES + 1)

    # ── 1. Size check ────────────────────────────────────────────────────────
    if len(raw) > settings.MAX_IMAGE_SIZE_BYTES:
        size_mb = len(raw) / (1024 * 1024)
        logger.warning("Upload rejected — size {:.1f} MB exceeds 15 MB limit.", size_mb)
        raise HTTPException(
            status_code=413,
            detail={
                "error": "FILE_TOO_LARGE",
                "message": f"Image size ({size_mb:.1f} MB) exceeds the 15 MB limit.",
            },
        )

    # ── 2. Magic bytes check ─────────────────────────────────────────────────
    if not (raw[:3] == _MAGIC_JPEG or raw[:8] == _MAGIC_PNG):
        logger.warning("Upload rejected — invalid image magic bytes.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_IMAGE_FORMAT",
                "message": "Only JPEG and PNG retinal fundus images are accepted.",
            },
        )

    # ── 3 & 4. Pillow decode (also enforces MAX_IMAGE_PIXELS) ────────────────
    try:
        with Image.open(io.BytesIO(raw)) as candidate:
            if candidate.width * candidate.height > Image.MAX_IMAGE_PIXELS:
                raise ValueError("Image dimensions exceed the pixel limit.")
            candidate.verify()  # Verify original file before converting to RGB.
        # Re-open after verify (verify() invalidates the object)
        image = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as exc:
        logger.warning("Upload rejected — image decode error: {}", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_IMAGE",
                "message": "The uploaded file could not be decoded as a valid image.",
            },
        ) from exc

    logger.debug(
        "Image validated: size={}x{}, bytes={}",
        image.width,
        image.height,
        len(raw),
    )
    return image, raw
