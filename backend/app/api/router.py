"""
NETRAVA — Master API Router
=============================
Aggregates all versioned sub-routers and mounts them under the correct
prefix paths.  Import and include ``api_router`` in ``main.py``.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.v1 import auth as auth_router
from backend.app.api.v1 import health as health_router
from backend.app.api.v1 import patients as patients_router
from backend.app.api.v1 import predict as predict_router
from backend.app.api.v1 import screening as screening_router

api_router = APIRouter()

# ── v1 routes ────────────────────────────────────────────────────────────────
api_router.include_router(health_router.router)
api_router.include_router(auth_router.router)
api_router.include_router(patients_router.router)
api_router.include_router(screening_router.router)
api_router.include_router(predict_router.router)

# Future routers (Phase 5+):
# from backend.app.api.v1 import reports, admin
# api_router.include_router(reports.router, prefix="/reports")
# api_router.include_router(admin.router, prefix="/admin")

