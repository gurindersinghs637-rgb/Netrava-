"""NETRAVA AI Model Inference Package.

Provides model loading, aspect-ratio-preserving retinal image preprocessing,
5-class Diabetic Retinopathy severity prediction, and Grad-CAM explainability.
"""

from .schemas import (
    CLASS_NAMES,
    ClassProbability,
    GradCAMResult,
    PredictionResult,
)
from .model_loader import (
    ModelLoader,
    ModelLoadError,
    CheckpointNotFoundError,
    get_model,
)
from .preprocessing import (
    ImagePreprocessor,
    ImageValidationError,
    ResizeWithPadding,
    get_eval_transform,
)
from .gradcam import GradCAM
from .predictor import NetravaPredictor

__all__ = [
    "CLASS_NAMES",
    "ClassProbability",
    "GradCAMResult",
    "PredictionResult",
    "ModelLoader",
    "ModelLoadError",
    "CheckpointNotFoundError",
    "get_model",
    "ImagePreprocessor",
    "ImageValidationError",
    "ResizeWithPadding",
    "get_eval_transform",
    "GradCAM",
    "NetravaPredictor",
]

