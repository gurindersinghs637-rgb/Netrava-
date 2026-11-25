"""Verify the production auth path with a controlled GoTrue transport."""
import httpx
import pytest
from backend.app.core.config import settings

@pytest.mark.parametrize("rejected", [False, True])
def test_login_token_is_forwarded_to_me(client, monkeypatch, rejected):
    """Login and /me must use the public key and the same access token."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://provider.invalid")
    monkeypatch.setattr(settings, "SUPABASE_KEY", "public-test")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "service-test")
    calls = []
    def handler(request):
        calls.append(request.url.path)
        if request.url.path == "/auth/v1/token":
            assert request.headers["apikey"] == "public-test"
            if rejected:
                return httpx.Response(400, json={"error": "invalid_grant"})
            return httpx.Response(200, json={"access_token": "controlled-token", "user": {"id": "user-1", "email": "test@example.com"}})
        if request.url.path == "/auth/v1/user":
            assert request.headers["apikey"] == "public-test"
            assert request.headers["authorization"] == "Bearer controlled-token"
            return httpx.Response(200, json={"id": "user-1", "email": "test@example.com"})
        assert request.url.path == "/rest/v1/user_profiles"
        assert request.headers["apikey"] == "service-test"
        assert request.headers["authorization"] == "Bearer service-test"
        assert request.url.params["id"] == "eq.user-1"
        return httpx.Response(200, json=[{"id": "user-1", "role": "technician", "clinic_id": "clinic-1", "full_name": "Test User", "is_active": True, "clinic": {"clinic_name": "Test Clinic", "is_active": True}}])
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
    response = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "test-password"})
    if rejected:
        assert response.status_code == 401
        assert response.json()["detail"]["error"] == "INVALID_CREDENTIALS"
        assert calls == ["/auth/v1/token"]
        return
    assert response.status_code == 200
    session = response.json()
    assert session["token_type"] == "bearer"
    me = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + session["access_token"]})
    assert me.status_code == 200
    assert me.json() == session["user"]
    assert "/auth/v1/user" in calls


@pytest.mark.parametrize("upstream,expected", [(401, 401), (403, 401), (500, 503), (429, 503)])
def test_provider_token_rejection_and_outage_are_distinct(client, monkeypatch, upstream, expected):
    """Provider outages must not be misreported as bad user tokens or leaked."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://provider.invalid")
    monkeypatch.setattr(settings, "SUPABASE_KEY", "public-test")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "service-test")
    original = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: httpx.Response(upstream, json={"message": "SENSITIVE_PROVIDER_BODY"}))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: original(transport=transport, **kw))
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid-test-token"})
    assert response.status_code == expected
    assert "SENSITIVE_PROVIDER_BODY" not in response.text


@pytest.mark.parametrize("active,clinic_active,role,expected", [(False, True, "technician", 403), (True, False, "technician", 403), (True, True, "owner", 403)])
def test_untrusted_or_inactive_membership_is_rejected(client, monkeypatch, active, clinic_active, role, expected):
    """Token validity alone never grants a clinic role."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://provider.invalid")
    monkeypatch.setattr(settings, "SUPABASE_KEY", "public-test")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "service-test")
    def handler(request):
        if request.url.path == "/auth/v1/user":
            return httpx.Response(200, json={"id": "user-1", "email": "test@example.com"})
        return httpx.Response(200, json=[{"id": "user-1", "role": role, "clinic_id": "clinic-1", "is_active": active, "clinic": {"clinic_name": "Clinic", "is_active": clinic_active}}])
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: original(transport=httpx.MockTransport(handler), **kw))
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer controlled-token"}).status_code == expected
