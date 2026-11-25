"""Normalized report mapping, isolation and PDF route regression tests."""
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from backend.app.services import report_service


class Query:
    """Capture query filters while supplying controlled persistence responses."""
    def __init__(self, rows):
        self.data = rows
        self.filters = []
    def select(self, *_args): return self
    def eq(self, key, value):
        self.filters.append((key, value))
        return self
    def limit(self, *_args): return self
    def execute(self): return self


@pytest.mark.asyncio
@pytest.mark.parametrize("outside", [False, True])
async def test_report_roundtrip_preserves_clinical_fields(monkeypatch, outside):
    """Urgency, original grade and override survive the normalized schema mapper."""
    from backend.app.core.config import settings
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://example.invalid")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "test-service")
    screening = Query([] if outside else [{"id": "screen"}])
    reports = Query([{"id": "report", "screening_id": "screen", "prediction_id": "prediction",
        "overall_grade": 2, "grade_override": 4, "clinical_assessment": "Reviewed", "is_urgent_referral": True,
        "review_status": "approved", "reviewed_at": "2026-11-13T10:00:00Z", "created_at": "2026-11-13T09:00:00Z", "updated_at": "2026-11-13T10:00:00Z"}])
    def table(name):
        if name == "reports":
            assert not outside, "No report query is allowed before clinic authorization"
            return reports
        return screening
    monkeypatch.setattr(report_service, "_admin_client", lambda: SimpleNamespace(table=table))
    if outside:
        with pytest.raises(HTTPException) as error:
            await report_service.get_report("screen", "clinic-b")
        assert error.value.status_code == 404
    else:
        result = await report_service.get_report("screen", "clinic-a")
        assert (result.overall_grade, result.grade_override, result.is_urgent_referral, result.is_signed_off) == (2, 4, True, True)
        assert result.updated_at > result.created_at
    assert ("clinic_id", "clinic-b" if outside else "clinic-a") in screening.filters


def test_pdf_download_is_authenticated_and_clinic_scoped(client, app, monkeypatch):
    """The PDF response is private and receives the trusted clinic identifier."""
    from backend.app.core.security import get_current_user, AuthenticatedUser
    assert client.get("/api/v1/screenings/screen/report/pdf").status_code == 401
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(id="staff", role="technician", clinic_id="clinic-a")
    async def render(screening_id, clinic_id):
        assert (screening_id, clinic_id) == ("screen", "clinic-a")
        return b"%PDF-test"
    monkeypatch.setattr(report_service, "get_report_pdf", render)
    try:
        response = client.get("/api/v1/screenings/screen/report/pdf")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.asyncio
async def test_pdf_uses_persisted_authorized_data(monkeypatch):
    """PDF generation consumes actual normalized values rather than default grades."""
    from backend.app.schemas.screening import ClinicalReportResponse
    async def report(*_args):
        return ClinicalReportResponse(id="report", screening_id="screen", prediction_id="pred", overall_grade=2, grade_override=3, is_urgent_referral=True, is_signed_off=True, created_at="2026-11-13T09:00:00Z", updated_at="2026-11-13T10:00:00Z")
    rows = {
        "screenings": [{"patient_id": "patient", "screening_date": "2026-11-13T09:00:00Z", "status": "completed"}],
        "patients": [{"id": "patient", "patient_code": "TEST", "full_name": "Synthetic Patient"}],
        "retinal_images": [{"id": "image", "eye_side": "right"}],
        "predictions": [{"id": "pred", "retinal_image_id": "image", "predicted_grade": 2, "confidence": .8, "referral_recommended": True}],
        "prediction_probabilities": [{"dr_grade": i, "probability": v} for i, v in enumerate([.05,.05,.8,.05,.05])],
    }
    monkeypatch.setattr(report_service, "get_report", report)
    monkeypatch.setattr(report_service, "_admin_client", lambda: SimpleNamespace(table=lambda name: Query(rows[name])))
    data = await report_service.get_report_pdf("screen", "clinic")
    assert data.startswith(b"%PDF-") and data.rstrip().endswith(b"%%EOF")
