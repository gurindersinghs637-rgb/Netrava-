"""Regression tests for the live Supabase profile and clinic column names."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from backend.app.core import security
from backend.app.services import auth_service


class _Response:
    def __init__(self, payload: Any, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> Any:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://supabase.example.invalid")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("test response", request=request, response=response)


class _FakeAsyncClient:
    responses: dict[str, _Response] = {}
    requests: list[tuple[str, dict[str, Any]]] = []

    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args) -> None:
        return None

    async def get(self, url: str, **kwargs) -> _Response:
        self.requests.append((url, kwargs))
        if url not in self.responses:
            raise AssertionError("Unexpected URL in mocked auth request.")
        return self.responses[url]


def test_profile_lookup_uses_live_is_active_and_clinic_name(monkeypatch) -> None:
    """The trusted profile lookup selects fields confirmed in live OpenAPI."""
    _FakeAsyncClient.requests = []
    _FakeAsyncClient.responses = {
        "https://supabase.example.invalid/rest/v1/user_profiles": _Response([{
            "id": "user-1",
            "role": "technician",
            "clinic_id": "clinic-1",
            "full_name": "Synthetic User",
            "is_active": True,
            "clinic": {"clinic_name": "Synthetic Clinic", "is_active": True},
        }]),
    }
    monkeypatch.setattr(auth_service.httpx, "AsyncClient", _FakeAsyncClient)

    profile = asyncio.run(auth_service.fetch_active_profile(
        user_id="user-1",
        url="https://supabase.example.invalid",
        service_key="test-only-key",
    ))

    assert profile["is_active"] is True
    assert profile["clinic"]["clinic_name"] == "Synthetic Clinic"
    params = _FakeAsyncClient.requests[0][1]["params"]
    assert "is_active" in params["select"]
    assert "clinic:clinics(clinic_name,is_active)" in params["select"]
    assert "active" not in params["select"].split(",")
    assert "clinics(name)" not in params["select"]


def test_inactive_live_profile_is_forbidden(monkeypatch) -> None:
    """An explicitly inactive live profile must not authenticate."""
    _FakeAsyncClient.responses = {
        "https://supabase.example.invalid/rest/v1/user_profiles": _Response([{
            "id": "user-1",
            "role": "technician",
            "clinic_id": "clinic-1",
            "is_active": False,
            "clinic": {"clinic_name": "Synthetic Clinic", "is_active": True},
        }]),
    }
    monkeypatch.setattr(auth_service.httpx, "AsyncClient", _FakeAsyncClient)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(auth_service.fetch_active_profile(
            user_id="user-1",
            url="https://supabase.example.invalid",
            service_key="test-only-key",
        ))
    assert exc_info.value.status_code == 403


def test_current_user_uses_shared_live_profile_loader(monkeypatch) -> None:
    """Bearer validation and clinic lookup use actual live profile column names."""
    from backend.app.core.config import settings

    url = "https://supabase.example.invalid"
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "SUPABASE_URL", url)
    monkeypatch.setattr(settings, "SUPABASE_KEY", "publishable-test-key")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "service-test-key")
    _FakeAsyncClient.requests = []
    _FakeAsyncClient.responses = {
        f"{url}/auth/v1/user": _Response({"id": "user-1", "email": "synthetic@example.test"}),
        f"{url}/rest/v1/user_profiles": _Response([{
            "id": "user-1",
            "role": "ophthalmologist",
            "clinic_id": "clinic-1",
            "full_name": "Synthetic Clinician",
            "is_active": True,
            "clinic": {"clinic_name": "Synthetic Clinic", "is_active": True},
        }]),
    }
    monkeypatch.setattr(security.httpx, "AsyncClient", _FakeAsyncClient)

    current = asyncio.run(security.get_current_user(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials="synthetic-access-token")
    ))

    assert current.id == "user-1"
    assert current.role == "ophthalmologist"
    assert current.clinic_id == "clinic-1"
    assert current.clinic_name == "Synthetic Clinic"
