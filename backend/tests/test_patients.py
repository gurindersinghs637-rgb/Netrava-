"""
NETRAVA — Tests: Patient Endpoints
=====================================
Tests for POST /api/v1/patients and GET /api/v1/patients.

In testing mode (no DB), all DB-requiring operations return 503.
Auth-requiring routes must return 401 without a valid token.
"""

from __future__ import annotations

import pytest


VALID_PATIENT = {
    "mrn": "MRN-2026-TEST001",
    "full_name": "Test Patient",
    "date_of_birth": "1980-01-15",
    "gender": "male",
    "diabetes_type": "type_2",
    "diabetes_duration_years": 5,
    "latest_hba1c": 7.5,
    "is_insulin_dependent": False,
}


def _auth_headers(client) -> dict:
    """Create a valid JWT for use in test requests."""
    from datetime import datetime, timezone, timedelta
    from jose import jwt

    token = jwt.encode(
        {
            "sub": "test-user-uuid-001",
            "exp": datetime.now(tz=timezone.utc) + timedelta(hours=1),
        },
        "test-secret-key-for-pytest-only",
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


# ── Auth enforcement ──────────────────────────────────────────────────────────

def test_create_patient_without_auth_returns_401(client):
    """POST /patients without token must return 401."""
    response = client.post("/api/v1/patients", json=VALID_PATIENT)
    assert response.status_code == 401


def test_list_patients_without_auth_returns_401(client):
    """GET /patients without token must return 401."""
    response = client.get("/api/v1/patients")
    assert response.status_code == 401


# ── Validation ────────────────────────────────────────────────────────────────

def test_create_patient_missing_fields_returns_422(client):
    """POST /patients without required fields must return 422."""
    headers = _auth_headers(client)
    response = client.post("/api/v1/patients", json={"mrn": "ONLY-MRN"}, headers=headers)
    assert response.status_code == 422


def test_create_patient_invalid_hba1c_returns_422(client):
    """POST /patients with HbA1c out of range (3–20) must return 422."""
    headers = _auth_headers(client)
    bad_patient = {**VALID_PATIENT, "latest_hba1c": 99.0}
    response = client.post("/api/v1/patients", json=bad_patient, headers=headers)
    assert response.status_code == 422


def test_create_patient_invalid_mrn_chars_returns_422(client):
    """POST /patients with special characters in MRN must return 422."""
    headers = _auth_headers(client)
    bad_patient = {**VALID_PATIENT, "mrn": "MRN@#$%INVALID"}
    response = client.post("/api/v1/patients", json=bad_patient, headers=headers)
    assert response.status_code == 422


def test_create_patient_invalid_gender_returns_422(client):
    """POST /patients with an invalid gender value must return 422."""
    headers = _auth_headers(client)
    bad_patient = {**VALID_PATIENT, "gender": "unknown"}
    response = client.post("/api/v1/patients", json=bad_patient, headers=headers)
    assert response.status_code == 422


# ── DB not configured — 503 expected ─────────────────────────────────────────

def test_create_patient_without_db_returns_503(client):
    """POST /patients with valid data but no DB configured must return 503."""
    headers = _auth_headers(client)
    response = client.post("/api/v1/patients", json=VALID_PATIENT, headers=headers)
    assert response.status_code == 503


def test_list_patients_without_db_returns_503(client):
    """GET /patients with valid auth but no DB configured must return 503."""
    headers = _auth_headers(client)
    response = client.get("/api/v1/patients", headers=headers)
    assert response.status_code == 503


# ── Query param validation ────────────────────────────────────────────────────

def test_list_patients_invalid_page_returns_422(client):
    """GET /patients with page=0 must return 422."""
    headers = _auth_headers(client)
    response = client.get("/api/v1/patients?page=0", headers=headers)
    assert response.status_code == 422


def test_list_patients_invalid_limit_returns_422(client):
    """GET /patients with limit=0 must return 422."""
    headers = _auth_headers(client)
    response = client.get("/api/v1/patients?limit=0", headers=headers)
    assert response.status_code == 422

