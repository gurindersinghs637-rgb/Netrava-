"""
NETRAVA — Common Pydantic Schemas
===================================
Shared response models used across all API routes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Structured error body returned for all 4xx / 5xx responses."""

    error: str = Field(..., description="SNAKE_CASE machine-readable error code.")
    message: str = Field(..., description="Human-readable description of the error.")

    model_config = {"json_schema_extra": {"example": {"error": "INVALID_IMAGE", "message": "The uploaded file is not a valid JPEG or PNG image."}}}


class HealthResponse(BaseModel):
    """Response body for GET /api/v1/health."""

    status: str = Field(..., description="'healthy' when the service is operational.")
    version: str = Field(..., description="Application version string.")
    device: str = Field(..., description="Compute device used by the model (cpu / cuda).")
    model_loaded: bool = Field(..., description="True when the model checkpoint was found on disk.")
    database_connected: bool = Field(..., description="True when the Supabase connection is verified.")
    timestamp: datetime = Field(..., description="UTC timestamp of the health check.")
    environment: Optional[str] = Field(None, description="Deployment environment name.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "device": "cpu",
                "model_loaded": True,
                "database_connected": False,
                "timestamp": "2026-11-01T12:00:00Z",
                "environment": "development",
            }
        }
    }

