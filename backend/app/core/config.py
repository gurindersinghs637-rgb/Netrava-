"""
NETRAVA — Application Configuration
=====================================
Loads all environment variables via Pydantic BaseSettings.
Never expose SUPABASE_SERVICE_ROLE_KEY or SECRET_KEY in API responses.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings.

    All values are read from environment variables (or a `.env` file).
    Defaults are safe for local development only.
    """

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Project identity ────────────────────────────────────────────────────
    PROJECT_NAME: str = "NETRAVA"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    NETRAVA_DISABLE_API_DOCS: bool = False

    # ── Security (NEVER expose in responses) ────────────────────────────────
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Supabase (NEVER expose SERVICE_ROLE_KEY to clients) ─────────────────
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""                  # anon / public key
    SUPABASE_SERVICE_ROLE_KEY: str = ""     # backend-only, never returned
    PASSWORD_RESET_REDIRECT_URL: str = ""  # Public HTTPS reset page URL; backend-only configuration.


    # ── AI Model ────────────────────────────────────────────────────────────
    MODEL_CHECKPOINT_PATH: str = "ai_model/checkpoint/best_efficientnet_b3_staged.pth"
    DEVICE: str = "cpu"
    MODEL_NUM_CLASSES: int = 5
    MODEL_INPUT_SIZE: int = 300

    # ── CORS ─────────────────────────────────────────────────────────────────
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
    ]

    # ── Image upload constraints ─────────────────────────────────────────────
    MAX_IMAGE_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png"]

    # ── Database (optional direct PostgreSQL connection) ─────────────────────
    DATABASE_URL: str = ""

    # ── Logging ──────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        allowed = {"development", "staging", "production", "testing"}
        if value not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return value

    @model_validator(mode="after")
    def require_production_secrets(self) -> "Settings":
        """Reject known development secrets in production configuration."""
        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY == "dev-secret-key-change-in-production" or len(self.SECRET_KEY) < 32:
                raise ValueError("Production requires a unique SECRET_KEY of at least 32 characters.")
            if not self.SUPABASE_URL or not self.SUPABASE_KEY or not self.SUPABASE_SERVICE_ROLE_KEY:
                raise ValueError("Production requires SUPABASE_URL, SUPABASE_KEY, and SUPABASE_SERVICE_ROLE_KEY.")
        return self

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "testing"

    @property
    def model_checkpoint_exists(self) -> bool:
        """Return True if the checkpoint file is present on disk."""
        return self.resolved_model_checkpoint_path.is_file()

    @property
    def resolved_model_checkpoint_path(self) -> Path:
        """Resolve relative model paths from the repository root, independent of cwd."""
        path = Path(self.MODEL_CHECKPOINT_PATH)
        if path.is_absolute():
            return path
        project_root = Path(__file__).resolve().parents[3]
        return (project_root / path).resolve()


# Module-level singleton — import this everywhere.
settings = Settings()

