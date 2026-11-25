"""Grad-CAM (Gradient-weighted Class Activation Mapping) for NETRAVA.

Hooks into the EfficientNet-B3 'conv_head' layer to produce visual activation
heatmaps highlighting lesions responsible for the predicted severity grade.
"""

import base64
import io
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import matplotlib.cm as cm
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

TARGET_LAYER_NAME = "conv_head"
DEFAULT_ALPHA = 0.40


class GradCAM:
    """Computes Grad-CAM heatmaps from the EfficientNet-B3 conv_head layer."""

    def __init__(
        self,
        model: nn.Module,
        target_layer: Optional[nn.Module] = None,
        layer_name: str = TARGET_LAYER_NAME,
    ) -> None:
        """Initialize Grad-CAM generator.

        Args:
            model: PyTorch model in eval mode.
            target_layer: The layer module to hook. If None, resolves model.conv_head.
            layer_name: Identifier of the target layer.
        """
        self.model = model
        self.layer_name = layer_name

        if target_layer is not None:
            self.target_layer = target_layer
        elif hasattr(model, layer_name):
            self.target_layer = getattr(model, layer_name)
        else:
            # Fallback search for conv_head in submodules
            found = dict(model.named_modules()).get(layer_name)
            if found is None:
                raise AttributeError(f"Target layer '{layer_name}' not found in model architecture.")
            self.target_layer = found

    def generate(
        self,
        input_tensor: torch.Tensor,
        display_image: Image.Image,
        target_class: Optional[int] = None,
        alpha: float = DEFAULT_ALPHA,
        colormap: str = "jet",
    ) -> Tuple[np.ndarray, Image.Image, float, float]:
        """Generates a Grad-CAM activation heatmap and blended overlay.

        Args:
            input_tensor: Input tensor of shape (1, 3, 300, 300).
            display_image: Padded 300x300 PIL Image to blend with heatmap.
            target_class: Target class index (0-4). If None, uses top predicted class.
            alpha: Opacity factor for the heatmap overlay (0.0 to 1.0).
            colormap: Matplotlib colormap name (default 'jet').

        Returns:
            A tuple of:
                - cam_normalized: 2D numpy array (300, 300) scaled to [0.0, 1.0]
                - overlay_image: 300x300 RGB PIL Image containing the blended heatmap
                - min_val: Minimum raw activation value before normalization
                - max_val: Maximum raw activation value before normalization
        """
        self.model.eval()
        captured: Dict[str, torch.Tensor] = {}

        def forward_hook(module: nn.Module, inputs: Any, output: torch.Tensor) -> None:
            captured["activation"] = output

        def backward_hook(module: nn.Module, grad_input: Any, grad_output: Any) -> None:
            captured["gradient"] = grad_output[0]

        forward_handle = self.target_layer.register_forward_hook(forward_hook)
        backward_handle = self.target_layer.register_full_backward_hook(backward_hook)

        try:
            # Ensure model parameters require gradients for backward pass
            with torch.enable_grad():
                # Forward pass
                self.model.zero_grad(set_to_none=True)
                # Clone tensor and enable grad on input if needed
                tensor_var = input_tensor.clone().detach().requires_grad_(True)
                logits = self.model(tensor_var)

                if target_class is None:
                    target_class = int(logits.argmax(dim=1).item())

                # Target score backpropagation
                target_score = logits[0, target_class]
                target_score.backward()

            activations = captured["activation"].detach()
            gradients = captured["gradient"].detach()

            # Global average pooling of gradients: (1, channels, 1, 1)
            weights = gradients.mean(dim=(2, 3), keepdim=True)

            # Linear combination of feature maps weighted by gradients
            cam = (weights * activations).sum(dim=1, keepdim=True)

            # Apply ReLU: only positive contributions to class of interest
            cam = F.relu(cam)

            # Bilinear interpolation to 300x300 image canvas
            h, w = display_image.size[1], display_image.size[0]
            cam = F.interpolate(cam, size=(h, w), mode="bilinear", align_corners=False)

            # Convert to numpy
            cam_np = cam[0, 0].cpu().numpy()
            min_val = float(cam_np.min())
            max_val = float(cam_np.max())

            # Normalize to [0.0, 1.0]
            denom = max_val - min_val
            if denom > 1e-8:
                cam_normalized = (cam_np - min_val) / denom
            else:
                cam_normalized = np.zeros_like(cam_np)

            # Generate pseudo-colored overlay using colormap
            try:
                import matplotlib
                if hasattr(matplotlib, "colormaps"):
                    cmap_fn = matplotlib.colormaps[colormap]
                else:
                    import matplotlib.cm as cm
                    cmap_fn = getattr(cm, "get_cmap")(colormap)
            except Exception:
                import matplotlib.pyplot as plt
                cmap_fn = plt.get_cmap(colormap)

            colored_heatmap = cmap_fn(cam_normalized)[:, :, :3]  # shape (H, W, 3), range [0, 1]
            colored_heatmap = (colored_heatmap * 255.0).astype(np.uint8)

            # Alpha blend with original display image
            base_np = np.array(display_image.convert("RGB"), dtype=np.float32)
            heatmap_np = colored_heatmap.astype(np.float32)
            blended = (1.0 - alpha) * base_np + alpha * heatmap_np
            blended = np.clip(blended, 0, 255).astype(np.uint8)
            overlay_image = Image.fromarray(blended)

            return cam_normalized, overlay_image, min_val, max_val

        finally:
            forward_handle.remove()
            backward_handle.remove()

    @staticmethod
    def to_base64(image: Image.Image, format: str = "PNG") -> str:
        """Encodes a PIL Image to a Base64 data string."""
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
