"""
NETRAVA — Backend Test Configuration
=======================================
pytest fixtures shared across all backend tests.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Force testing environment BEFORE app import (settings reads env at import time)
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only"
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = ""
os.environ.setdefault("MODEL_CHECKPOINT_PATH", "ai_model/checkpoint/best_efficientnet_b3_staged.pth")
os.environ.setdefault("DEVICE", "cpu")


@pytest.fixture(scope="session")
def app():
    """Return the FastAPI application instance (session-scoped)."""
    from backend.app.main import app as _app
    return _app


@pytest.fixture(scope="session")
def client(app):
    """Return a synchronous TestClient (session-scoped)."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

