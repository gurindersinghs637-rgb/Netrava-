"""
NETRAVA — Tests: Screening Endpoint
======================================
Tests for POST /api/v1/screenings

Covers:
- Auth enforcement (401 without token)
- Invalid file format rejection (400)
- Oversized file rejection (413)
- Valid JPEG upload with no DB configured (503)
"""

from __future__ import annotations

import io
from datetime import datetime, timezone, timedelta

import pytest
from PIL import Image


def _make_jpeg_bytes(width: int = 300, height: int = 300) -> bytes:
    img = Image.new("RGB", (width, height), color=(180, 100, 80))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _auth_headers(client) -> dict:
    from jose import jwt
    token = jwt.encode(
        {"sub": "tech-user-uuid", "exp": datetime.now(tz=timezone.utc) + timedelta(hours=1)},
        "test-secret-key-for-pytest-only",
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def test_screening_without_auth_returns_401(client):
    """POST /screenings without token must return 401."""
    raw = _make_jpeg_bytes()
    response = client.post(
        "/api/v1/screenings",
        data={"patient_id": "some-uuid", "eye": "OD"},
        files={"image": ("fundus.jpg", io.BytesIO(raw), "image/jpeg")},
    )
    assert response.status_code == 401


def test_screening_invalid_image_format_rejected(client):
    """POST /screenings with a GIF file must return 400."""
    headers = _auth_headers(client)
    fake_gif = b"GIF89a" + b"\x00" * 100  # GIF magic bytes
    response = client.post(
        "/api/v1/screenings",
        data={"patient_id": "some-uuid", "eye": "OD"},
        files={"image": ("fundus.gif", io.BytesIO(fake_gif), "image/gif")},
        headers=headers,
    )
    assert response.status_code == 400


def test_screening_oversized_file_rejected(client):
    """POST /screenings with a >15 MB file must return 413."""
    headers = _auth_headers(client)
    real_jpeg = _make_jpeg_bytes()
    oversized = real_jpeg + b"\x00" * (16 * 1024 * 1024)
    response = client.post(
        "/api/v1/screenings",
        data={"patient_id": "some-uuid", "eye": "OD"},
        files={"image": ("big.jpg", io.BytesIO(oversized), "image/jpeg")},
        headers=headers,
    )
    assert response.status_code == 413


def test_screening_invalid_eye_value_returns_422(client):
    """POST /screenings with eye='BOTH' must return 422."""
    headers = _auth_headers(client)
    raw = _make_jpeg_bytes()
    response = client.post(
        "/api/v1/screenings",
        data={"patient_id": "some-uuid", "eye": "BOTH"},
        files={"image": ("fundus.jpg", io.BytesIO(raw), "image/jpeg")},
        headers=headers,
    )
    assert response.status_code == 422


def test_screening_valid_sharp_image_no_db_returns_503_or_success(client):
    """POST /screenings with a valid sharp image:
    - If DB is not configured: 503 (storage error during upload).
    - The endpoint must NOT crash (no 500 from an unhandled exception).
    """
    headers = _auth_headers(client)
    # Large solid image — high blur_score (infinite variance for solid colors is high)
    raw = _make_jpeg_bytes(width=500, height=500)
    response = client.post(
        "/api/v1/screenings",
        data={"patient_id": "test-patient-uuid", "eye": "OD"},
        files={"image": ("fundus.jpg", io.BytesIO(raw), "image/jpeg")},
        headers=headers,
    )
    assert response.status_code == 503, (
        f"Without configured storage/database, no screening may be reported as saved: {response.text}"
    )


def test_only_ophthalmologist_can_submit_report(client):
    """A technician identity must not be able to submit a clinical grade review."""
    response = client.post(
        "/api/v1/screenings/00000000-0000-0000-0000-000000000001/report",
        headers=_auth_headers(client),
        json={"overall_grade": 1},
    )
    assert response.status_code == 403


def test_qc_marks_uniform_image_ungradable_and_reports_dark_illumination():
    """QC must reject a flat image and flag its underexposed brightness."""
    from backend.app.services.screening_service import _assess_qc

    assessment = _assess_qc(Image.new("RGB", (128, 128), color=(10, 10, 10)))
    assert assessment.is_gradable is False
    assert assessment.blur_score == 0
    assert assessment.illumination == "underexposed"


def test_qc_accepts_sharp_checkerboard_image():
    """High-frequency edges should produce a sharpness score above the threshold."""
    from backend.app.services.screening_service import _assess_qc

    image = Image.new("RGB", (128, 128), color="black")
    pixels = image.load()
    for y in range(128):
        for x in range(128):
            if (x // 4 + y // 4) % 2:
                pixels[x, y] = (220, 220, 220)

    assessment = _assess_qc(image)
    assert assessment.is_gradable is True
    assert assessment.blur_score >= 50

