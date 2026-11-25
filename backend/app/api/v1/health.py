"""
NETRAVA — Health Check Router
================================
GET /api/v1/health — public, no authentication required.

Returns service status, model readiness, and database connectivity.
This endpoint is used by load balancers, monitoring tools, and the
Flutter frontend to confirm the backend is operational before making
inference requests.
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx
from fastapi import APIRouter
from loguru import logger

from backend.app.core.config import settings
from backend.app.ml.model_bridge import is_predictor_initialised
from backend.app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


async def _database_probe() -> bool:
    """Perform a small read-only Supabase REST request when configured."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(
                f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/clinics",
                params={"select": "id", "limit": "1"},
                headers={
                    "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                },
            )
        return response.status_code == 200
    except httpx.HTTPError as exc:
        logger.warning("Database health probe failed: {}", type(exc).__name__)
        return False


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
    description=(
        "Returns the operational status of the NETRAVA backend service, "
        "including model readiness and database connectivity. "
        "No authentication required."
    ),
)
async def health_check() -> HealthResponse:
    """Return service health status.

    Checks:
    - Whether the AI model checkpoint file exists on disk.
    - Whether a read-only request to the configured Supabase REST API succeeds.
    """
    model_loaded = is_predictor_initialised()
    database_connected = False if settings.is_testing else await _database_probe()
    service_ready = model_loaded and (database_connected or settings.is_testing)

    logger.debug(
        "Health check: model_loaded={}, database_connected={}",
        model_loaded,
        database_connected,
    )

    return HealthResponse(
        status="healthy" if service_ready else "degraded",
        version=settings.VERSION,
        device=settings.DEVICE,
        model_loaded=model_loaded,
        database_connected=database_connected,
        timestamp=datetime.now(tz=timezone.utc),
        environment=settings.ENVIRONMENT,
    )

