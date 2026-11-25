"""
NETRAVA — Loguru Logging Configuration
========================================
Configures structured JSON logging for production and human-readable
colourised output for development.  Also intercepts the standard library
``logging`` module so that third-party libraries (uvicorn, sqlalchemy, etc.)
are routed through Loguru.

Usage::

    from backend.app.core.logging import configure_logging
    configure_logging()   # call once at application startup

After that, everywhere in the codebase use::

    from loguru import logger
    logger.info("Something happened", extra={"key": "value"})
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    pass


class _InterceptHandler(logging.Handler):
    """Route stdlib ``logging`` records through Loguru."""

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover
        # Map stdlib level to Loguru level name
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find the correct caller frame so Loguru reports the right source.
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def configure_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """Configure Loguru for the application.

    Args:
        log_level: Minimum severity level (e.g. ``"DEBUG"``, ``"INFO"``).
        json_logs: When True, emit newline-delimited JSON (for production /
            log aggregators).  When False, emit colourised human text.
    """
    # Remove Loguru's default handler so we control the format entirely.
    logger.remove()

    if json_logs:
        # Structured JSON — one object per line.
        logger.add(
            sys.stdout,
            level=log_level,
            serialize=True,          # Loguru serialises each record to JSON
            backtrace=False,
            diagnose=False,
        )
    else:
        fmt = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        logger.add(
            sys.stdout,
            level=log_level,
            format=fmt,
            colorize=True,
            backtrace=False,
            diagnose=False,
        )

    # Intercept stdlib logging (uvicorn, httpx, sqlalchemy, …)
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
    for name in logging.root.manager.loggerDict:  # type: ignore[attr-defined]
        logging.getLogger(name).handlers = [_InterceptHandler()]
        logging.getLogger(name).propagate = False

    # HTTP transport logs can include signed URLs, identifiers and headers.
    for name in ("httpx", "httpcore", "postgrest", "storage3", "gotrue", "supabase_auth"):
        logging.getLogger(name).setLevel(logging.WARNING)

    logger.debug("Logging configured — level={}, json={}", log_level, json_logs)

