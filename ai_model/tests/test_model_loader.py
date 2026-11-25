"""Automated tests for ModelLoader and checkpoint integrity."""

from pathlib import Path
import pytest
import torch
import torch.nn as nn

from ai_model.inference.model_loader import (
    DEFAULT_CHECKPOINT_PATH,
    CheckpointNotFoundError,
    ModelLoadError,
    ModelLoader,
    get_model,
)


class TestModelLoader:
    """Test suite verifying checkpoint loading, weight mapping, and error handling."""

    def test_default_checkpoint_exists(self) -> None:
        """Verify the physical checkpoint file exists at the expected path."""
        assert DEFAULT_CHECKPOINT_PATH.exists(), f"Missing checkpoint: {DEFAULT_CHECKPOINT_PATH}"
        assert DEFAULT_CHECKPOINT_PATH.stat().st_size > 40_000_000, "Checkpoint file size unexpectedly small."

    def test_load_trained_model_successfully(self) -> None:
        """Verify the trained EfficientNet-B3 model loads strictly into eval mode."""
        loader = ModelLoader(checkpoint_path=DEFAULT_CHECKPOINT_PATH, device="cpu")
        model = loader.load(strict=True)

        assert isinstance(model, nn.Module)
        assert not model.training, "Model must be in eval() mode after loading."
        assert loader.device == torch.device("cpu")

    def test_checkpoint_metadata_extracted(self) -> None:
        """Verify checkpoint metadata fields match documented training parameters."""
        loader = ModelLoader(checkpoint_path=DEFAULT_CHECKPOINT_PATH, device="cpu")
        loader.load()

        metadata = loader.metadata
        assert metadata["model_name"] == "efficientnet_b3"
        assert metadata["img_size"] == 300
        assert metadata["epoch"] == 20
        assert metadata["best_val_qwk"] > 0.85
        assert len(metadata["class_names"]) == 5

    def test_model_output_dimensions(self) -> None:
        """Verify forward pass on (1, 3, 300, 300) tensor produces (1, 5) logits."""
        loader = ModelLoader(checkpoint_path=DEFAULT_CHECKPOINT_PATH, device="cpu")
        model = loader.get_model()

        dummy_tensor = torch.randn(1, 3, 300, 300)
        with torch.no_grad():
            output = model(dummy_tensor)

        assert output.shape == (1, 5), f"Unexpected output shape: {output.shape}"
        assert not torch.isnan(output).any(), "Model produced NaN outputs."

    def test_invalid_checkpoint_path_raises_error(self, tmp_path: Path) -> None:
        """Verify non-existent checkpoint path raises CheckpointNotFoundError."""
        invalid_path = tmp_path / "non_existent_checkpoint.pth"
        loader = ModelLoader(checkpoint_path=invalid_path, device="cpu")

        with pytest.raises(CheckpointNotFoundError) as exc_info:
            loader.load()
        assert "not found" in str(exc_info.value).lower()

    def test_singleton_get_model_accessor(self) -> None:
        """Verify get_model() returns an operational model instance."""
        model = get_model(device="cpu")
        assert isinstance(model, nn.Module)
        assert hasattr(model, "conv_head")
        assert hasattr(model, "classifier")

