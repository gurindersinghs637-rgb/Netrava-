"""
NETRAVA — Tests: Health Endpoint
==================================
Tests for GET /api/v1/health

All tests run with no DB / Supabase configured (testing environment).
"""

from __future__ import annotations

from datetime import datetime


def test_health_returns_200(client):
    """Health endpoint must return 200 OK."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


def test_health_response_schema(client):
    """Health response must contain all documented fields."""
    response = client.get("/api/v1/health")
    body = response.json()

    required_fields = {"status", "version", "device", "model_loaded", "database_connected", "timestamp"}
    missing = required_fields - body.keys()
    assert not missing, f"Missing fields in health response: {missing}"


def test_health_status_reports_degraded_when_model_is_not_loaded(client):
    """Testing startup skips model warm-up and must not claim full readiness."""
    response = client.get("/api/v1/health")
    assert response.json()["status"] == "degraded"


def test_health_version_matches(client):
    """Health response 'version' must be a non-empty string."""
    response = client.get("/api/v1/health")
    version = response.json()["version"]
    assert isinstance(version, str) and len(version) > 0


def test_health_device_field(client):
    """Health response 'device' must be a non-empty string."""
    response = client.get("/api/v1/health")
    device = response.json()["device"]
    assert isinstance(device, str) and len(device) > 0


def test_health_model_loaded_is_bool(client):
    """Health 'model_loaded' must be a boolean."""
    response = client.get("/api/v1/health")
    assert isinstance(response.json()["model_loaded"], bool)


def test_health_model_loaded_is_false_when_testing(client):
    """The test lifespan skips model warm-up, so readiness remains false."""
    response = client.get("/api/v1/health")
    assert response.json()["model_loaded"] is False


def test_health_timestamp_is_valid_iso(client):
    """Health 'timestamp' must be a parseable ISO 8601 datetime string."""
    response = client.get("/api/v1/health")
    ts_str = response.json()["timestamp"]
    try:
        datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except ValueError:
        pytest.fail(f"timestamp '{ts_str}' is not a valid ISO 8601 datetime.")


def test_health_database_connected_is_bool(client):
    """'database_connected' must be a boolean (False in test environment)."""
    response = client.get("/api/v1/health")
    assert isinstance(response.json()["database_connected"], bool)


def test_health_no_auth_required(client):
    """Health endpoint must be accessible without an Authorization header."""
    # Default TestClient has no auth header set
    response = client.get("/api/v1/health")
    assert response.status_code == 200

