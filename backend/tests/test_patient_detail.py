"""Tests for clinic-scoped patient detail retrieval against live column names."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend.app.services import patient_service


class _PatientQuery:
    def __init__(self, rows):
        self.rows = rows
        self.selected = ""
        self.filters = []
        self.limit_value = None

    def select(self, fields):
        self.selected = fields
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows)


class _PatientClient:
    def __init__(self, rows):
        self.query = _PatientQuery(rows)

    def table(self, name):
        assert name == "patients"
        return self.query


def test_get_patient_selects_live_columns_and_scopes_clinic(monkeypatch):
    client = _PatientClient([{
        "id": "patient-1",
        "patient_code": "P-001",
        "full_name": "Synthetic Patient",
        "date_of_birth": "1980-01-02",
        "sex": "female",
        "phone": None,
        "email": None,
        "medical_notes": None,
        "clinic_id": "clinic-1",
        "created_by": "user-1",
        "created_at": "2026-11-03T10:00:00Z",
        "updated_at": "2026-11-03T10:00:00Z",
    }])
    monkeypatch.setattr(patient_service, "_get_admin_client", lambda: client)
    monkeypatch.setattr(patient_service.settings, "SUPABASE_URL", "https://example.invalid")
    monkeypatch.setattr(patient_service.settings, "SUPABASE_SERVICE_ROLE_KEY", "test-only")

    result = asyncio.run(patient_service.get_patient("patient-1", "clinic-1"))

    assert result.patient_code == "P-001"
    assert ("id", "patient-1") in client.query.filters
    assert ("clinic_id", "clinic-1") in client.query.filters
    assert "patient_code" in client.query.selected
    assert "mrn" not in client.query.selected


def test_get_patient_returns_not_found_for_other_clinic(monkeypatch):
    client = _PatientClient([])
    monkeypatch.setattr(patient_service, "_get_admin_client", lambda: client)
    monkeypatch.setattr(patient_service.settings, "SUPABASE_URL", "https://example.invalid")
    monkeypatch.setattr(patient_service.settings, "SUPABASE_SERVICE_ROLE_KEY", "test-only")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(patient_service.get_patient("patient-1", "clinic-2"))

    assert exc_info.value.status_code == 404
