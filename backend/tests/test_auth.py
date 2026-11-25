"""
NETRAVA — Tests: Authentication Endpoints
==========================================
Tests for POST /api/v1/auth/login and GET /api/v1/auth/me.

In testing mode, Supabase is not configured, so:
- Login must return 503 (service unavailable) — not a crash.
- /auth/me without a token must return 401.
- /auth/me with an invalid token must return 401.
"""

from __future__ import annotations

import pytest


def test_login_without_body_returns_422(client):
    """POST /auth/login without a body must return 422 Unprocessable Entity."""
    response = client.post("/api/v1/auth/login", json={})
    assert response.status_code == 422


def test_login_with_invalid_email_returns_422(client):
    """POST /auth/login with malformed email must return 422."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "not-an-email", "password": "SomePass123!"},
    )
    assert response.status_code == 422


def test_login_with_short_password_returns_422(client):
    """POST /auth/login with password < 8 chars must return 422."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@netrava.clinic", "password": "short"},
    )
    assert response.status_code == 422


def test_login_without_supabase_returns_503(client):
    """POST /auth/login when Supabase is not configured must return 503."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@netrava.clinic", "password": "ValidPass123!"},
    )
    # In testing env, SUPABASE_URL is empty → 503 Service Unavailable
    assert response.status_code == 503
    body = response.json()
    assert "error" in body or "detail" in body


def test_auth_me_without_token_returns_401(client):
    """GET /auth/me without Authorization header must return 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_auth_me_with_invalid_token_returns_401(client):
    """GET /auth/me with a garbage Bearer token must return 401."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer this.is.not.a.valid.jwt"},
    )
    assert response.status_code == 401


def test_auth_me_with_expired_token_returns_401(client):
    """GET /auth/me with a structurally valid but expired JWT must return 401."""
    from datetime import datetime, timezone
    from jose import jwt

    expired_token = jwt.encode(
        {"sub": "user-123", "exp": 1000000000},  # year 2001 — definitely expired
        "test-secret-key-for-pytest-only",
        algorithm="HS256",
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


def test_auth_me_error_body_has_error_field(client):
    """401 error response must contain an 'error' or 'detail' field."""
    response = client.get("/api/v1/auth/me")
    body = response.json()
    assert "error" in body or "detail" in body


def test_non_test_auth_fails_closed_without_supabase(client, monkeypatch):
    """Local development must not accept locally signed tokens as Supabase users."""
    from datetime import datetime, timezone, timedelta
    from jose import jwt
    from backend.app.core.config import settings

    token = jwt.encode(
        {"sub": "attacker-controlled", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 503

