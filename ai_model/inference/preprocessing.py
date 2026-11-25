"""Image Preprocessing Module for NETRAVA.

Implements the exact training-time transforms:
- Aspect-ratio preserving thumbnail resize using LANCZOS interpolation
- Black zero-padding to 300 x 300 square canvas
- ImageNet channel normalization (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
- Conversion to PyTorch tensor format (1, 3, 300, 300)
"""

import io
from pathlib import Path
from typing import BinaryIO, Tuple, Union

import numpy as np
import torch
from PIL import Image, ImageOps
from torchvision import transforms

DEFAULT_IMG_SIZE = 300
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


class ImageValidationError(ValueError):
    """Raised when an input image is invalid, corrupt, or unreadable."""
    pass


class ResizeWithPadding:
    """Aspect-ratio-preserving resize that centers the image on a black canvas."""

    def __init__(self, size: int = DEFAULT_IMG_SIZE, fill: Tuple[int, int, int] = (0, 0, 0)) -> None:
        self.size = size
        self.fill = fill

    def __call__(self, image: Image.Image) -> Image.Image:
        image = image.convert("RGB")
        image.thumbnail((self.size, self.size), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (self.size, self.size), self.fill)
        left = (self.size - image.width) // 2
        top = (self.size - image.height) // 2
        canvas.paste(image, (left, top))
        return canvas


def get_eval_transform(img_size: int = DEFAULT_IMG_SIZE) -> transforms.Compose:
    """Returns the PyTorch transform pipeline used during model evaluation."""
    return transforms.Compose([
        ResizeWithPadding(img_size),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


class ImagePreprocessor:
    """High-level image preprocessor validating inputs and producing evaluation tensors."""

    def __init__(self, img_size: int = DEFAULT_IMG_SIZE) -> None:
        self.img_size = img_size
        self.resize_with_padding = ResizeWithPadding(img_size)
        self.eval_transform = get_eval_transform(img_size)

    def load_image(self, input_data: Union[str, Path, bytes, BinaryIO, Image.Image]) -> Image.Image:
        """Loads and validates a retinal fundus image from various input types.

        Args:
            input_data: File path, raw bytes, file-like binary stream, or existing PIL Image.

        Returns:
            Validated PIL Image in RGB mode.

        Raises:
            ImageValidationError: If image cannot be decoded or is invalid.
        """
        if isinstance(input_data, Image.Image):
            return input_data.convert("RGB")

        if isinstance(input_data, (str, Path)):
            path = Path(input_data)
            if not path.exists():
                raise ImageValidationError(f"Image file does not exist: {path}")
            try:
                with Image.open(path) as img:
                    return img.convert("RGB")
            except Exception as exc:
                raise ImageValidationError(f"Failed to open image file '{path}': {exc}") from exc

        if isinstance(input_data, bytes):
            if len(input_data) == 0:
                raise ImageValidationError("Empty image byte payload received.")
            try:
                with Image.open(io.BytesIO(input_data)) as img:
                    return img.convert("RGB")
            except Exception as exc:
                raise ImageValidationError(f"Failed to decode image from bytes: {exc}") from exc

        if hasattr(input_data, "read"):
            try:
                with Image.open(input_data) as img:
                    return img.convert("RGB")
            except Exception as exc:
                raise ImageValidationError(f"Failed to read image stream: {exc}") from exc

        raise ImageValidationError(f"Unsupported input data type: {type(input_data)}")

    def preprocess(
        self,
        input_data: Union[str, Path, bytes, BinaryIO, Image.Image],
    ) -> Tuple[torch.Tensor, Image.Image]:
        """Validates, resizes, pads, and normalizes an input fundus image.

        Args:
            input_data: File path, bytes, or PIL Image.

        Returns:
            A tuple of:
                - input_tensor: Normalized torch.Tensor of shape (1, 3, img_size, img_size)
                - display_image: Preprocessed PIL Image (300 x 300) for display/Grad-CAM overlay.
        """
        raw_image = self.load_image(input_data)

        # 1. Padded canvas image for display / Grad-CAM blending
        display_image = self.resize_with_padding(raw_image)

        # 2. Normalized tensor for model forward pass
        tensor = self.eval_transform(raw_image)  # shape: (3, img_size, img_size)
        input_tensor = tensor.unsqueeze(0)        # shape: (1, 3, img_size, img_size)

        return input_tensor, display_image

