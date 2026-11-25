"""
NETRAVA — FastAPI Application Entry Point
==========================================
Creates and configures the FastAPI application instance.

Architecture (from docs/architecture/backend_architecture.md):
- Pattern: Repository-Service-Controller (RSC)
- Routers are thin; all business logic lives in app/services/
- ML bridge lives in app/ml/ — never duplicate ai_model/ code
- Global error format: {"error": "SNAKE_CASE_CODE", "message": "Human readable"}
- CORS origins are loaded from settings (never hard-coded)
- Model warm-up happens in the lifespan context manager

Usage:
    uvicorn backend.app.main:app --port 8000 --reload
    (from project root, with PYTHONPATH=.)
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.core.logging import configure_logging


# ── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle manager.

    Startup tasks:
    - Configure logging (JSON in production, colourised in development).
    - Log configuration summary (no secrets).
    - Verify model checkpoint presence (warm-up deferred to Phase 1 bridge).

    Shutdown tasks:
    - Flush Loguru sinks.
    """
    # ── Startup ──────────────────────────────────────────────────────────────
    json_logs = settings.is_production
    configure_logging(log_level=settings.LOG_LEVEL, json_logs=json_logs)

    logger.info(
        "NETRAVA backend starting up | version={} | environment={} | device={}",
        settings.VERSION,
        settings.ENVIRONMENT,
        settings.DEVICE,
    )

    if settings.is_testing:
        logger.info("Testing environment: model warm-up skipped.")
    elif settings.model_checkpoint_exists:
        logger.info("Model checkpoint found: {}", settings.resolved_model_checkpoint_path)
        # Warm up the ML predictor singleton
        try:
            from backend.app.ml.model_bridge import initialise_predictor
            initialise_predictor()
        except Exception as exc:
            logger.warning("Model warm-up failed (inference will be unavailable): {}", type(exc).__name__)
    else:
        logger.warning(
            "Model checkpoint NOT found at '{}'. "
            "Inference endpoints will be unavailable.",
            settings.resolved_model_checkpoint_path,
        )

    yield  # Application runs here

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("NETRAVA backend shutting down.")


# ── Application factory ───────────────────────────────────────────────────────

def create_application() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "Explainable AI-Based Diabetic Retinopathy Screening System. "
            "See. Detect. Explain."
        ),
        openapi_url=None if settings.NETRAVA_DISABLE_API_DOCS else f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # ── Request timing middleware ─────────────────────────────────────────────
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):  # type: ignore[no-untyped-def]
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        route = request.scope.get("route")
        route_path = getattr(route, "path", "<unmatched>")
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        logger.debug(
            "{} {} → {} ({:.1f} ms)",
            request.method,
            route_path,
            response.status_code,
            elapsed_ms,
        )
        return response

    # ── Global exception handlers ─────────────────────────────────────────────

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        route = request.scope.get("route")
        route_path = getattr(route, "path", "<unmatched>")
        safe_errors = [
            {"type": str(err.get("type", "")), "loc": [str(part) for part in err.get("loc", [])]}
            for err in exc.errors()
        ]
        logger.warning("Validation error on {} {}: {}", request.method, route_path, safe_errors)
        # Do not log or return submitted field values; validation may include secrets or health data.
        safe_details = [
            {
                "type": str(err.get("type", "")),
                "loc": [str(l) for l in err.get("loc", [])],
                "msg": str(err.get("msg", "")),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": safe_details,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        route = request.scope.get("route")
        route_path = getattr(route, "path", "<unmatched>")
        logger.error("Unhandled exception on {} {}: {}", request.method, route_path, type(exc).__name__)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
            },
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


# Module-level app instance (used by uvicorn and pytest).
app = create_application()

