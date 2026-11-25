"""
NETRAVA — Tests: Image Validation (ML Bridge)
===============================================
Tests for app.ml.image_validator.validate_and_load_image

Covers:
- Valid JPEG accepted
- Valid PNG accepted
- File too large rejected with 413
- Invalid magic bytes rejected with 400
- Corrupted image rejected with 400
"""

from __future__ import annotations

import io
import struct

import pytest
from fastapi import UploadFile
from PIL import Image


def _make_jpeg_bytes(width: int = 100, height: int = 100) -> bytes:
    """Return raw JPEG bytes for a solid red image."""
    img = Image.new("RGB", (width, height), color=(200, 50, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_png_bytes(width: int = 100, height: int = 100) -> bytes:
    """Return raw PNG bytes for a solid blue image."""
    img = Image.new("RGB", (width, height), color=(50, 50, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_upload_file(content: bytes, filename: str = "test.jpg") -> UploadFile:
    """Wrap raw bytes in a FastAPI UploadFile."""
    return UploadFile(filename=filename, file=io.BytesIO(content))


# ── Valid images ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_valid_jpeg_accepted():
    """A valid JPEG image must be accepted and returned as a PIL Image."""
    from backend.app.ml.image_validator import validate_and_load_image

    raw = _make_jpeg_bytes()
    upload = _make_upload_file(raw, "fundus.jpg")
    pil_img, returned_bytes = await validate_and_load_image(upload)

    assert pil_img.mode == "RGB"
    assert returned_bytes == raw


@pytest.mark.asyncio
async def test_valid_png_accepted():
    """A valid PNG image must be accepted and returned as a PIL Image."""
    from backend.app.ml.image_validator import validate_and_load_image

    raw = _make_png_bytes()
    upload = _make_upload_file(raw, "fundus.png")
    pil_img, returned_bytes = await validate_and_load_image(upload)

    assert pil_img.mode == "RGB"
    assert returned_bytes == raw


# ── Size enforcement ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_oversized_file_rejected():
    """A file exceeding 15 MB must raise HTTPException 413."""
    from fastapi import HTTPException
    from backend.app.ml.image_validator import validate_and_load_image

    # Start with valid JPEG header then pad with zeros to exceed 15 MB
    real_jpeg = _make_jpeg_bytes()
    oversized = real_jpeg + b"\x00" * (16 * 1024 * 1024)  # ~16 MB
    upload = _make_upload_file(oversized, "huge.jpg")

    with pytest.raises(HTTPException) as exc_info:
        await validate_and_load_image(upload)

    assert exc_info.value.status_code == 413


# ── Magic bytes enforcement ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_magic_bytes_rejected():
    """A file with non-JPEG/PNG magic bytes must raise HTTPException 400."""
    from fastapi import HTTPException
    from backend.app.ml.image_validator import validate_and_load_image

    fake_content = b"BM" + b"\x00" * 1000  # BMP magic bytes
    upload = _make_upload_file(fake_content, "fake.bmp")

    with pytest.raises(HTTPException) as exc_info:
        await validate_and_load_image(upload)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_empty_file_rejected():
    """An empty file must raise HTTPException 400."""
    from fastapi import HTTPException
    from backend.app.ml.image_validator import validate_and_load_image

    upload = _make_upload_file(b"", "empty.jpg")

    with pytest.raises(HTTPException) as exc_info:
        await validate_and_load_image(upload)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_corrupted_jpeg_rejected():
    """A file with JPEG magic bytes but corrupted body must raise HTTPException 400."""
    from fastapi import HTTPException
    from backend.app.ml.image_validator import validate_and_load_image

    # Valid JPEG header, garbage body
    corrupt = b"\xff\xd8\xff" + b"\x00\x11\x22\x33" * 50
    upload = _make_upload_file(corrupt, "corrupt.jpg")

    with pytest.raises(HTTPException) as exc_info:
        await validate_and_load_image(upload)

    assert exc_info.value.status_code == 400



@pytest.mark.asyncio
async def test_upload_read_is_bounded():
    """Reject oversized uploads without reading their entire contents into memory."""
    from backend.app.core.config import settings
    from backend.app.ml.image_validator import validate_and_load_image
    from fastapi import HTTPException
    class LargeUpload:
        async def read(self, size):
            assert size == settings.MAX_IMAGE_SIZE_BYTES + 1
            return b"x" * size
    with pytest.raises(HTTPException) as error:
        await validate_and_load_image(LargeUpload())
    assert error.value.status_code == 413
