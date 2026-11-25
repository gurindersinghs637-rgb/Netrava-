"""Regression tests that keep user-supplied values out of logs and errors."""

from __future__ import annotations

import io
from datetime import date

import pytest
from fastapi import HTTPException, UploadFile
from loguru import logger


def test_validation_error_does_not_echo_or_log_submitted_value(client) -> None:
    """Malformed fields can contain passwords or clinical values; omit their values."""
    output = io.StringIO()
    sink_id = logger.add(output, format="{message}", level="WARNING")
    marker = "DO_NOT_LOG_VALIDATION_VALUE"
    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": marker, "password": "invalid"},
        )
    finally:
        logger.remove(sink_id)

    assert response.status_code == 422
    assert marker not in response.text
    assert marker not in output.getvalue()
    assert "email" in response.text


@pytest.mark.asyncio
async def test_rejected_upload_does_not_log_filename() -> None:
    """Filenames may contain patient identifiers and must not enter logs."""
    from backend.app.ml.image_validator import validate_and_load_image

    output = io.StringIO()
    sink_id = logger.add(output, format="{message}", level="WARNING")
    marker = "DO_NOT_LOG_PATIENT_FILENAME"
    upload = UploadFile(filename=marker, file=io.BytesIO(b"not-an-image"))
    try:
        with pytest.raises(HTTPException) as exc_info:
            await validate_and_load_image(upload)
    finally:
        logger.remove(sink_id)

    assert exc_info.value.status_code == 400
    assert marker not in output.getvalue()


@pytest.mark.asyncio
async def test_patient_database_error_does_not_log_exception_text(monkeypatch) -> None:
    """Database exception messages can contain query values; log only the type."""
    from backend.app.services import patient_service
    from backend.app.schemas.patients import CreatePatientRequest

    class BrokenQuery:
        def execute(self):
            raise RuntimeError("DO_NOT_LOG_DATABASE_DETAIL")

    class BrokenClient:
        def rpc(self, *_args, **_kwargs):
            return BrokenQuery()

    monkeypatch.setattr(patient_service.settings, "SUPABASE_URL", "https://example.invalid")
    monkeypatch.setattr(patient_service.settings, "SUPABASE_SERVICE_ROLE_KEY", "test-only-key")
    monkeypatch.setattr(patient_service, "_get_admin_client", lambda: BrokenClient())

    request = CreatePatientRequest(
        mrn="TEST-001",
        full_name="Test Patient",
        date_of_birth=date(1980, 1, 1),
        gender="female",
        diabetes_type="type_2",
    )
    output = io.StringIO()
    sink_id = logger.add(output, format="{message}", level="ERROR")
    try:
        with pytest.raises(HTTPException) as exc_info:
            await patient_service.create_patient(
                request=request,
                registered_by="00000000-0000-0000-0000-000000000001",
                clinic_id="00000000-0000-0000-0000-000000000002",
            )
    finally:
        logger.remove(sink_id)

    assert exc_info.value.status_code == 503
    assert "RuntimeError" in output.getvalue()
    assert "DO_NOT_LOG_DATABASE_DETAIL" not in output.getvalue()
