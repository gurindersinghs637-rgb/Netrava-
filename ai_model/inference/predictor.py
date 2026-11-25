"""Complete Prediction Engine for NETRAVA Diabetic Retinopathy System.

Orchestrates image preprocessing, EfficientNet-B3 model forward pass,
5-class probability calculation, and optional Grad-CAM explainability.
"""

import time
from pathlib import Path
from typing import BinaryIO, Optional, Union

import torch
from PIL import Image

from .gradcam import GradCAM
from .model_loader import ModelLoader
from .preprocessing import ImagePreprocessor
from .schemas import (
    CLASS_NAMES,
    CLINICAL_RECOMMENDATIONS,
    ClassProbability,
    GradCAMResult,
    PredictionResult,
)


class NetravaPredictor:
    """End-to-end inference engine for Diabetic Retinopathy screening."""

    def __init__(
        self,
        checkpoint_path: Optional[Union[str, Path]] = None,
        device: Optional[Union[str, torch.device]] = None,
    ) -> None:
        """Initialize the predictor.

        Args:
            checkpoint_path: Path to best_efficientnet_b3_staged.pth.
            device: Compute device ('cuda', 'cpu'). Auto-selects if None.
        """
        self.loader = ModelLoader(checkpoint_path=checkpoint_path, device=device)
        self.model = self.loader.load()
        self.device = self.loader.device
        self.preprocessor = ImagePreprocessor(img_size=300)
        self.gradcam = GradCAM(model=self.model, layer_name="conv_head")

    def predict(
        self,
        input_data: Union[str, Path, bytes, BinaryIO, Image.Image],
        return_gradcam: bool = True,
        save_overlay_path: Optional[Union[str, Path]] = None,
        gradcam_alpha: float = 0.40,
    ) -> PredictionResult:
        """Executes full diagnostic screening pipeline on an input fundus image.

        Args:
            input_data: Image file path, raw bytes, binary stream, or PIL Image.
            return_gradcam: Whether to compute and attach Grad-CAM heatmap explanation.
            save_overlay_path: Optional path to persist the blended heatmap overlay image.
            gradcam_alpha: Heatmap blend opacity (0.0 to 1.0).

        Returns:
            PredictionResult containing 5-class probabilities, severity classification,
            confidence score, inference latency, and Grad-CAM explanation.
        """
        # 1. Preprocess input image (aspect-ratio padding + ImageNet normalization)
        input_tensor, display_image = self.preprocessor.preprocess(input_data)
        input_tensor = input_tensor.to(self.device)

        # 2. Execute timed forward inference
        start_time = time.perf_counter()
        with torch.no_grad():
            logits = self.model(input_tensor)
            probabilities_tensor = torch.softmax(logits, dim=1)[0]
        end_time = time.perf_counter()

        inference_time_ms = round((end_time - start_time) * 1000, 2)

        # 3. Extract probabilities and top prediction
        probs_list = probabilities_tensor.cpu().tolist()
        logits_list = logits[0].cpu().tolist()

        predicted_grade = int(torch.argmax(probabilities_tensor).item())
        confidence_score = round(float(probs_list[predicted_grade]), 4)
        severity_label = CLASS_NAMES[predicted_grade]
        is_referral_recommended = bool(predicted_grade >= 2)
        recommendation = CLINICAL_RECOMMENDATIONS[predicted_grade]

        class_probabilities = [
            ClassProbability(
                grade=idx,
                class_name=CLASS_NAMES[idx],
                probability=round(float(prob), 5),
            )
            for idx, prob in enumerate(probs_list)
        ]

        # 4. Compute Grad-CAM explainability if requested
        explanation_result: Optional[GradCAMResult] = None
        if return_gradcam:
            cam_norm, overlay_img, min_val, max_val = self.gradcam.generate(
                input_tensor=input_tensor,
                display_image=display_image,
                target_class=predicted_grade,
                alpha=gradcam_alpha,
            )

            overlay_path_str: Optional[str] = None
            if save_overlay_path:
                save_path = Path(save_overlay_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                overlay_img.save(save_path, format="PNG")
                overlay_path_str = str(save_path.resolve())

            explanation_result = GradCAMResult(
                target_layer="conv_head",
                heatmap_min=round(min_val, 4),
                heatmap_max=round(max_val, 4),
                heatmap_base64=self.gradcam.to_base64(overlay_img),
                overlay_saved_path=overlay_path_str,
            )

        return PredictionResult(
            predicted_grade=predicted_grade,
            severity_label=severity_label,
            confidence_score=confidence_score,
            is_referral_recommended=is_referral_recommended,
            clinical_recommendation=recommendation,
            probabilities=class_probabilities,
            raw_logits=[round(l, 4) for l in logits_list],
            inference_time_ms=inference_time_ms,
            device_used=str(self.device),
            model_name="efficientnet_b3",
            explanation=explanation_result,
        )

