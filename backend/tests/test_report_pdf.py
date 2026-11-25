"""Tests for local synthetic PDF rendering and mocked private-storage upload."""

from __future__ import annotations

import io
import sys
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from PIL import Image
from pydantic import ValidationError

from backend.app.services import report_pdf


def _heatmap_png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (48, 32), color=(30, 180, 120)).save(buffer, format="PNG")
    return buffer.getvalue()


def _synthetic_report(**changes) -> report_pdf.ClinicalReportDocument:
    data = {
        "report_id": "report-test-001",
        "generated_at": datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc),
        "clinic_name": "Synthetic Clinic",
        "patient_id": "patient-test-001",
        "patient_code": "SYN-001",
        "patient_name": "Synthetic Patient",
        "date_of_birth": date(1980, 1, 2),
        "sex": "female",
        "screening_id": "screening-test-001",
        "screening_date": datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc),
        "screening_status": "reviewed",
        "retinal_image_ids": ["image-test-001"],
        "eye_sides": ["OD"],
        "prediction_id": "prediction-test-001",
        "predicted_grade": 2,
        "confidence": 0.72,
        "referral_recommended": True,
        "probabilities": [
            {"grade": 0, "probability": 0.03},
            {"grade": 1, "probability": 0.08},
            {"grade": 2, "probability": 0.72},
            {"grade": 3, "probability": 0.12},
            {"grade": 4, "probability": 0.05},
        ],
        "clinical_assessment": "Synthetic assessment only; not a real patient record.",
        "gradcam_png": _heatmap_png(),
    }
    data.update(changes)
    return report_pdf.ClinicalReportDocument(**data)


def test_pdf_renderer_creates_valid_pdf_from_synthetic_data() -> None:
    """The renderer returns a complete PDF without contacting external services."""
    pdf_bytes = report_pdf.render_clinical_report_pdf(_synthetic_report())

    assert pdf_bytes.startswith(b"%PDF-")
    assert pdf_bytes.rstrip().endswith(b"%%EOF")
    assert len(pdf_bytes) > 2_000


def test_pdf_renderer_rejects_incomplete_probability_distribution() -> None:
    """A report cannot omit grades or use probabilities that do not sum to one."""
    with pytest.raises(ValidationError):
        _synthetic_report(probabilities=[{"grade": 0, "probability": 1.0}])
    with pytest.raises(ValidationError):
        _synthetic_report(probabilities=[
            {"grade": 0, "probability": 0.5},
            {"grade": 1, "probability": 0.1},
            {"grade": 2, "probability": 0.1},
            {"grade": 3, "probability": 0.1},
            {"grade": 4, "probability": 0.1},
        ])


def test_pdf_renderer_enforces_referral_threshold() -> None:
    """Referral status must agree with the unchanged grade >= 2 rule."""
    with pytest.raises(ValidationError):
        _synthetic_report(predicted_grade=1, referral_recommended=True)


@pytest.mark.asyncio
async def test_pdf_upload_uses_private_bucket_and_returns_signed_url(monkeypatch) -> None:
    """PDF upload is exercised with an in-memory Storage mock only."""
    calls = []

    class FakeStorage:
        def upload(self, path, contents, options):
            calls.append(("upload", path, contents, options))
            return {"path": path}

        def create_signed_url(self, path, expires_in):
            calls.append(("sign", path, expires_in))
            return {"signedURL": "https://signed.example.invalid/report.pdf"}

        def remove(self, paths):
            calls.append(("remove", paths))

    class FakeStorageRoot:
        def from_(self, bucket_name):
            assert bucket_name == "clinical-reports"
            return FakeStorage()

    fake_module = SimpleNamespace(create_client=lambda *_args: SimpleNamespace(storage=FakeStorageRoot()))
    monkeypatch.setitem(sys.modules, "supabase", fake_module)
    monkeypatch.setattr(report_pdf.settings, "SUPABASE_URL", "https://example.invalid")
    monkeypatch.setattr(report_pdf.settings, "SUPABASE_SERVICE_ROLE_KEY", "test-only-key")

    path, signed_url = await report_pdf.upload_report_pdf(
        report_id="00000000-0000-0000-0000-000000000001",
        clinic_id="00000000-0000-0000-0000-000000000002",
        pdf_bytes=b"%PDF-1.4\nsynthetic",
    )

    assert path.startswith("00000000-0000-0000-0000-000000000002/00000000-0000-0000-0000-000000000001/")
    assert path.endswith(".pdf")
    assert signed_url == "https://signed.example.invalid/report.pdf"
    assert calls[0][0] == "upload"
    assert calls[0][3] == {"content-type": "application/pdf", "upsert": "false"}
    assert calls[1] == ("sign", path, 1800)


@pytest.mark.asyncio
async def test_pdf_upload_rejects_invalid_uuid_before_storage(monkeypatch) -> None:
    """Untrusted identifiers cannot be used to construct object paths."""
    monkeypatch.setattr(report_pdf.settings, "SUPABASE_URL", "https://example.invalid")
    monkeypatch.setattr(report_pdf.settings, "SUPABASE_SERVICE_ROLE_KEY", "test-only-key")
    with pytest.raises(HTTPException) as exc_info:
        await report_pdf.upload_report_pdf(
            report_id="../../bad",
            clinic_id="00000000-0000-0000-0000-000000000002",
            pdf_bytes=b"%PDF-1.4\nsynthetic",
        )
    assert exc_info.value.status_code == 422
