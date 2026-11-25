"""Model Loader for NETRAVA EfficientNet-B3 Diabetic Retinopathy System.

Loads the trained staged checkpoint safely, reconstructs the architecture,
and provides a validated, thread-safe inference-ready PyTorch model.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import timm
import torch
import torch.nn as nn

DEFAULT_CHECKPOINT_PATH = Path(__file__).resolve().parent.parent / "checkpoint" / "best_efficientnet_b3_staged.pth"
EXPECTED_MODEL_NAME = "efficientnet_b3"
NUM_CLASSES = 5
DROP_RATE = 0.30


class ModelLoadError(Exception):
    """Raised when model initialization or weight loading fails."""
    pass


class CheckpointNotFoundError(FileNotFoundError):
    """Raised when the specified model checkpoint file does not exist."""
    pass


class ModelLoader:
    """Encapsulates loading, validating, and caching the trained EfficientNet-B3 model."""

    def __init__(
        self,
        checkpoint_path: Optional[Union[str, Path]] = None,
        device: Optional[Union[str, torch.device]] = None,
    ) -> None:
        """Initialize the model loader.

        Args:
            checkpoint_path: Path to the .pth checkpoint file. Defaults to DEFAULT_CHECKPOINT_PATH.
            device: Compute device ('cuda', 'cpu', or torch.device). If None, auto-selects CUDA if available.
        """
        self.checkpoint_path = Path(checkpoint_path or DEFAULT_CHECKPOINT_PATH).resolve()

        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        self._model: Optional[nn.Module] = None
        self._metadata: Dict[str, Any] = {}

    @property
    def metadata(self) -> Dict[str, Any]:
        """Metadata extracted from the loaded checkpoint."""
        return self._metadata

    def load(self, strict: bool = True) -> nn.Module:
        """Loads and verifies the model.

        Args:
            strict: Enforce strict key matching when loading state_dict.

        Returns:
            The loaded PyTorch model in eval() mode.

        Raises:
            CheckpointNotFoundError: If checkpoint file does not exist.
            ModelLoadError: If architecture reconstruction or weight loading fails.
        """
        if not self.checkpoint_path.exists():
            raise CheckpointNotFoundError(
                f"Checkpoint file not found at: {self.checkpoint_path}. "
                "Ensure the trained weights 'best_efficientnet_b3_staged.pth' are present."
            )

        try:
            # 1. Instantiate the documented architecture
            model = timm.create_model(
                EXPECTED_MODEL_NAME,
                pretrained=False,
                num_classes=NUM_CLASSES,
                drop_rate=DROP_RATE,
            )

            # 2. Load checkpoint payload safely
            checkpoint = torch.load(
                self.checkpoint_path,
                map_location=self.device,
                weights_only=False,
            )

            # 3. Extract state_dict and metadata
            if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                state_dict = checkpoint["model_state_dict"]
                self._metadata = {
                    "epoch": checkpoint.get("epoch"),
                    "best_val_qwk": checkpoint.get("best_val_qwk"),
                    "seed": checkpoint.get("seed"),
                    "model_name": checkpoint.get("model_name", EXPECTED_MODEL_NAME),
                    "img_size": checkpoint.get("img_size", 300),
                    "class_names": checkpoint.get("class_names", {}),
                }
            elif isinstance(checkpoint, dict):
                state_dict = checkpoint
                self._metadata = {"model_name": EXPECTED_MODEL_NAME}
            else:
                raise ModelLoadError(
                    f"Unexpected checkpoint payload type: {type(checkpoint)}. "
                    "Expected dict containing state_dict."
                )

            # 4. Load weights into architecture
            load_result = model.load_state_dict(state_dict, strict=strict)

            # 5. Move to target device and set to eval mode
            model = model.to(self.device)
            model.eval()

            # 6. Validate output dimension with dummy tensor
            dummy_input = torch.zeros(1, 3, 300, 300, device=self.device)
            with torch.no_grad():
                output = model(dummy_input)

            if output.shape != (1, NUM_CLASSES):
                raise ModelLoadError(
                    f"Invalid model output dimensions: {output.shape}. "
                    f"Expected (1, {NUM_CLASSES})."
                )

            self._model = model
            return self._model

        except CheckpointNotFoundError:
            raise
        except Exception as exc:
            raise ModelLoadError(
                f"Failed to reconstruct or load model from '{self.checkpoint_path}': {exc}"
            ) from exc

    def get_model(self) -> nn.Module:
        """Returns the loaded model, initializing it if not already loaded."""
        if self._model is None:
            return self.load()
        return self._model


# Module-level singleton cache
_LOADER_INSTANCE: Optional[ModelLoader] = None


def get_model(
    checkpoint_path: Optional[Union[str, Path]] = None,
    device: Optional[Union[str, torch.device]] = None,
) -> nn.Module:
    """Convenience accessor returning a thread-safe singleton model instance."""
    global _LOADER_INSTANCE
    if _LOADER_INSTANCE is None:
        _LOADER_INSTANCE = ModelLoader(checkpoint_path=checkpoint_path, device=device)
        return _LOADER_INSTANCE.load()
    return _LOADER_INSTANCE.get_model()

