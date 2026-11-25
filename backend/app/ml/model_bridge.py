"""
NETRAVA — ML Bridge: Model Loader Singleton
=============================================
Thin wrapper around ai_model.inference.model_loader that:
  - Provides a singleton accessor for the backend service layer.
  - Initialises the model on the correct device from settings.
  - Centralises concurrency locking for Grad-CAM backward passes.
  - NEVER duplicates ai_model/ inference logic.

All heavy ML code lives in ai_model/inference/.
This module only wires that code into the FastAPI lifecycle.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from loguru import logger

from backend.app.core.config import settings

# ── Lazy imports (ai_model may not be on PYTHONPATH in unit test environments)
_predictor_instance: Optional[object] = None
_lock: asyncio.Lock = asyncio.Lock()


def _build_predictor() -> object:
    """Construct a NetravaPredictor using project settings."""
    import sys
    from pathlib import Path

    # Ensure project root is importable
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from ai_model.inference.predictor import NetravaPredictor  # type: ignore

    predictor = NetravaPredictor(
        checkpoint_path=settings.resolved_model_checkpoint_path,
        device=settings.DEVICE,
    )
    logger.info(
        "NetravaPredictor initialised | checkpoint={} | device={}",
        settings.resolved_model_checkpoint_path,
        settings.DEVICE,
    )
    return predictor


def get_predictor() -> object:
    """Return the module-level NetravaPredictor singleton.

    Raises:
        RuntimeError: If the predictor has not been initialised via
            ``initialise_predictor()`` first.
    """
    global _predictor_instance
    if _predictor_instance is None:
        raise RuntimeError(
            "ML predictor is not initialised. "
            "Call initialise_predictor() during application startup."
        )
    return _predictor_instance


def is_predictor_initialised() -> bool:
    """Return whether the predictor singleton is ready for inference."""
    return _predictor_instance is not None


def initialise_predictor() -> None:
    """Build and cache the predictor singleton.

    Called once from the FastAPI lifespan startup handler.
    Safe to call multiple times (idempotent).
    """
    global _predictor_instance
    if _predictor_instance is not None:
        logger.debug("Predictor already initialised — skipping.")
        return
    _predictor_instance = _build_predictor()


def get_gradcam_lock() -> asyncio.Lock:
    """Return the shared asyncio.Lock for serialising Grad-CAM backward passes.

    Grad-CAM modifies gradient tensors which is not thread-safe. Callers must
    acquire this lock before running any backward pass.

    Usage::

        async with get_gradcam_lock():
            result = predictor.predict_with_gradcam(image)
    """
    return _lock

