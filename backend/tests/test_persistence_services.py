"""Offline tests for transactional Supabase persistence RPC contracts."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest


class FakeRPCClient:
    def __init__(self, data):
        self.data = data
        self.calls = []

    def rpc(self, name, payload):
        self.calls.append((name, payload))
        return SimpleNamespace(execute=lambda: SimpleNamespace(data=self.data))


class FakeStorageBucket:
    def __init__(self, calls):
        self.calls = calls

    def upload(self, path, contents, options):
        self.calls.append(("upload", path, contents, options))

    def create_signed_url(self, path, expires_in):
        self.calls.append(("signed_url", path, expires_in))
        return {"signedURL": "https://storage.example.test/signed"}


class FakeStorage:
    def __init__(self, calls):
        self.calls = calls

    def from_(self, bucket_name):
        self.calls.append(("bucket", bucket_name))
        return FakeStorageBucket(self.calls)


class FakeStorageClient:
    def __init__(self):
        self.calls = []
        self.storage = FakeStorage(self.calls)


def _configured(monkeypatch):
    from backend.app.core.config import settings

    monkeypatch.setattr(settings, "SUPABASE_URL", "https://local-test.invalid")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "test-only-service-key")


def test_patient_search_strips_filter_grammar_but_keeps_names():
    from backend.app.services.patient_service import _sanitize_search

    assert _sanitize_search("  José Kumar,)%") == "José Kumar"


@pytest.mark.asyncio
async def test_patient_create_uses_transactional_clinic_rpc(monkeypatch):
    from backend.app.schemas.patients import CreatePatientRequest
    from backend.app.services import patient_service

    _configured(monkeypatch)
    client = FakeRPCClient({
        "id": "00000000-0000-0000-0000-000000000010",
        "mrn": "MRN-10",
        "full_name": "Example Patient",
        "registered_by": "00000000-0000-0000-0000-000000000011",
        "created_at": "2026-11-03T10:00:00+00:00",
    })
    monkeypatch.setattr(patient_service, "_get_admin_client", lambda: client)
    request = CreatePatientRequest(
        mrn="mrn-10",
        full_name="Example Patient",
        date_of_birth=date(1980, 1, 1),
        gender="female",
        diabetes_type="type_2",
    )

    result = await patient_service.create_patient(
        request=request,
        registered_by="00000000-0000-0000-0000-000000000011",
        clinic_id="00000000-0000-0000-0000-000000000012",
    )

    assert result.id.endswith("10")
    assert client.calls[0][0] == "register_clinic_patient"
    assert client.calls[0][1]["p_patient"]["clinic_id"].endswith("12")


@pytest.mark.asyncio
async def test_prediction_persistence_uses_audit_rpc(monkeypatch):
    import supabase
    from backend.app.services import prediction_service

    _configured(monkeypatch)
    client = FakeRPCClient({"id": "00000000-0000-0000-0000-000000000020"})
    monkeypatch.setattr(supabase, "create_client", lambda *_args: client)

    result = await prediction_service._save_prediction(
        retinal_image_id="00000000-0000-0000-0000-000000000021",
        predicted_grade=2,
        confidence=0.75,
        inference_ms=123.4,
        probabilities=[0.01, 0.04, 0.75, 0.15, 0.05],
        requested_by="00000000-0000-0000-0000-000000000022",
        clinic_id="00000000-0000-0000-0000-000000000023",
        heatmap_path="clinic/image.png",
    )

    assert result.endswith("20")
    assert client.calls[0][0] == "write_screening_prediction"
    assert client.calls[0][1]["p_prediction"]["clinic_id"].endswith("23")


@pytest.mark.asyncio
async def test_screening_records_use_transactional_rpc(monkeypatch):
    import supabase
    from backend.app.schemas.screening import QCAssessment
    from backend.app.services import screening_service

    _configured(monkeypatch)
    client = FakeRPCClient({"screening_id": "screening-id", "retinal_image_id": "image-id"})
    monkeypatch.setattr(supabase, "create_client", lambda *_args: client)

    await screening_service._save_screening_records(
        screening_id="00000000-0000-0000-0000-000000000040",
        retinal_image_id="00000000-0000-0000-0000-000000000041",
        patient_id="00000000-0000-0000-0000-000000000042",
        eye="OD",
        technician_id="00000000-0000-0000-0000-000000000043",
        clinic_id="00000000-0000-0000-0000-000000000044",
        qc=QCAssessment(is_gradable=True, blur_score=120.0, illumination="optimal", confidence=0.9),
        storage_path="clinic/image.jpg",
    )

    assert client.calls[0][0] == "create_screening_records"
    assert client.calls[0][1]["p_image"]["storage_path"] == "clinic/image.jpg"


@pytest.mark.asyncio
async def test_fundus_upload_uses_clinic_path_and_signed_url(monkeypatch):
    import supabase
    from backend.app.services import screening_service

    _configured(monkeypatch)
    client = FakeStorageClient()
    monkeypatch.setattr(supabase, "create_client", lambda *_args: client)

    url = await screening_service._upload_fundus_image(
        raw_bytes=b"verified-test-image",
        retinal_image_id="image-id",
        clinic_id="clinic-id",
        image_format="PNG",
    )

    assert url.endswith("/signed")
    assert any(call[0] == "upload" and call[1] == "clinic-id/image-id.png" for call in client.calls)


@pytest.mark.asyncio
async def test_gradcam_upload_uses_clinic_path_and_signed_url(monkeypatch):
    import supabase
    from backend.app.services import prediction_service

    _configured(monkeypatch)
    client = FakeStorageClient()
    monkeypatch.setattr(supabase, "create_client", lambda *_args: client)

    url, storage_path = await prediction_service._upload_gradcam(
        gradcam_bytes=b"test-overlay",
        retinal_image_id="image-id",
        clinic_id="clinic-id",
    )

    assert url is not None and url.endswith("/signed")
    assert storage_path.startswith("clinic-id/image-id/") and storage_path.endswith(".png")
    assert any(call[0] == "upload" and call[1] == storage_path for call in client.calls)


@pytest.mark.asyncio
async def test_report_submit_uses_atomic_audit_rpc(monkeypatch):
    from backend.app.schemas.screening import ReviewRequest
    from backend.app.services import report_service

    _configured(monkeypatch)
    report = {
        "id": "00000000-0000-0000-0000-000000000030",
        "screening_id": "00000000-0000-0000-0000-000000000031",
        "ophthalmologist_id": "00000000-0000-0000-0000-000000000032",
        "overall_grade": 2,
        "grade_override": None,
        "ophthalmologist_notes": None,
        "is_urgent_referral": False,
        "is_signed_off": True,
        "signed_off_at": "2026-11-03T10:00:00+00:00",
        "created_at": "2026-11-03T10:00:00+00:00",
        "updated_at": "2026-11-03T10:00:00+00:00",
    }
    client = FakeRPCClient(report)
    monkeypatch.setattr(report_service, "_admin_client", lambda: client)

    result = await report_service.submit_review(
        screening_id=report["screening_id"],
        clinic_id="00000000-0000-0000-0000-000000000033",
        ophthalmologist_id=report["ophthalmologist_id"],
        request=ReviewRequest(overall_grade=2, is_signed_off=True),
    )

    assert result.id.endswith("30")
    assert client.calls[0][0] == "write_screening_review"


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["patient", "screening", "prediction", "report"])
async def test_missing_rpc_never_falls_back_to_partial_table_writes(monkeypatch, operation):
    """Missing transactional functions must never trigger unaudited direct writes."""
    import supabase
    from fastapi import HTTPException
    from backend.app.services import patient_service, screening_service, prediction_service, report_service
    from backend.app.schemas.patients import CreatePatientRequest
    from backend.app.schemas.screening import QCAssessment, ReviewRequest
    class MissingRPC(Exception):
        code = "PGRST202"
    class Client:
        table_calls = []
        def rpc(self, *_args):
            raise MissingRPC("Could not find the function")
        def table(self, name):
            self.table_calls.append(name)
            raise AssertionError("Direct table access after missing RPC")
    _configured(monkeypatch)
    client = Client()
    monkeypatch.setattr(supabase, "create_client", lambda *_args: client)
    monkeypatch.setattr(patient_service, "_get_admin_client", lambda: client)
    monkeypatch.setattr(report_service, "_admin_client", lambda: client)
    with pytest.raises((HTTPException, MissingRPC)) as error:
        if operation == "patient":
            await patient_service.create_patient(CreatePatientRequest(mrn="TEST-01", full_name="Test Patient", date_of_birth=date(1980, 1, 1), gender="female", diabetes_type="type_2"), "user", "clinic")
        elif operation == "screening":
            await screening_service._save_screening_records("screen", "image", "patient", "OD", "user", "clinic", QCAssessment(is_gradable=True, blur_score=100, illumination="optimal", confidence=1), "clinic/image.png")
        elif operation == "prediction":
            await prediction_service._save_prediction("image", 2, .8, 12, [.05,.05,.8,.05,.05], "user", "clinic", None)
        else:
            await report_service.submit_review("screen", "clinic", "user", ReviewRequest(overall_grade=2))
    if isinstance(error.value, HTTPException):
        assert error.value.status_code == 503
    assert client.table_calls == []
