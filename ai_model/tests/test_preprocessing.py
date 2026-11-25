"""Automated tests for ImagePreprocessor and ResizeWithPadding transform."""

import io
from pathlib import Path
import numpy as np
import pytest
import torch
from PIL import Image

from ai_model.inference.preprocessing import (
    DEFAULT_IMG_SIZE,
    ImagePreprocessor,
    ImageValidationError,
    ResizeWithPadding,
)

SAMPLE_IMAGE_PATH = Path(__file__).resolve().parent / "data" / "000c1434d8d7.png"


class TestPreprocessing:
    """Test suite verifying aspect-ratio padding, normalization, and validation."""

    def test_resize_with_padding_wide_image(self) -> None:
        """Verify wide aspect ratio image is padded top and bottom with black pixels."""
        resizer = ResizeWithPadding(size=300, fill=(0, 0, 0))
        wide_img = Image.new("RGB", (600, 300), color=(255, 100, 50))
        padded_img = resizer(wide_img)

        assert padded_img.size == (300, 300)
        # Top-left corner must be black padding (0, 0, 0)
        assert padded_img.getpixel((0, 0)) == (0, 0, 0)
        # Center pixel must contain the original image color
        assert padded_img.getpixel((150, 150)) == (255, 100, 50)

    def test_resize_with_padding_tall_image(self) -> None:
        """Verify tall aspect ratio image is padded left and right with black pixels."""
        resizer = ResizeWithPadding(size=300, fill=(0, 0, 0))
        tall_img = Image.new("RGB", (300, 600), color=(50, 150, 255))
        padded_img = resizer(tall_img)

        assert padded_img.size == (300, 300)
        # Top-left corner must be black padding
        assert padded_img.getpixel((0, 0)) == (0, 0, 0)
        # Center pixel must contain the original image color
        assert padded_img.getpixel((150, 150)) == (50, 150, 255)

    def test_preprocess_from_file_path(self) -> None:
        """Verify preprocessing from real fundus image file path."""
        if not SAMPLE_IMAGE_PATH.exists():
            pytest.skip(f"Sample test image not found at: {SAMPLE_IMAGE_PATH}")

        preprocessor = ImagePreprocessor(img_size=DEFAULT_IMG_SIZE)
        tensor, display_img = preprocessor.preprocess(SAMPLE_IMAGE_PATH)

        assert isinstance(tensor, torch.Tensor)
        assert tensor.shape == (1, 3, 300, 300)
        assert tensor.dtype == torch.float32
        assert isinstance(display_img, Image.Image)
        assert display_img.size == (300, 300)

    def test_preprocess_from_raw_bytes(self) -> None:
        """Verify preprocessing from in-memory JPEG/PNG image bytes."""
        img = Image.new("RGB", (400, 400), color=(180, 70, 40))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        raw_bytes = buf.getvalue()

        preprocessor = ImagePreprocessor(img_size=DEFAULT_IMG_SIZE)
        tensor, display_img = preprocessor.preprocess(raw_bytes)

        assert tensor.shape == (1, 3, 300, 300)
        assert display_img.size == (300, 300)

    def test_preprocess_from_pil_image(self) -> None:
        """Verify preprocessing from direct PIL Image instance."""
        pil_img = Image.new("RGB", (512, 512), color=(100, 150, 200))
        preprocessor = ImagePreprocessor(img_size=DEFAULT_IMG_SIZE)
        tensor, display_img = preprocessor.preprocess(pil_img)

        assert tensor.shape == (1, 3, 300, 300)
        assert display_img.size == (300, 300)

    def test_invalid_image_raises_validation_error(self) -> None:
        """Verify corrupted bytes and empty payloads raise ImageValidationError."""
        preprocessor = ImagePreprocessor(img_size=DEFAULT_IMG_SIZE)

        with pytest.raises(ImageValidationError):
            preprocessor.preprocess(b"")

        with pytest.raises(ImageValidationError):
            preprocessor.preprocess(b"NOT_A_VALID_IMAGE_DATA")

        with pytest.raises(ImageValidationError):
            preprocessor.preprocess(Path("non_existent_retina.jpg"))

