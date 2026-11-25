"""Pydantic data schemas and constants for NETRAVA inference."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

# International Clinical Diabetic Retinopathy (ICDR) Scale Mapping
CLASS_NAMES: Dict[int, str] = {
    0: "No DR",
    1: "Mild",
    2: "Moderate",
    3: "Severe",
    4: "Proliferative DR",
}

SEVERITY_DESCRIPTIONS: Dict[int, str] = {
    0: "No microaneurysms or diabetic retinal abnormalities detected.",
    1: "Microaneurysms only. Regular glycemic monitoring recommended.",
    2: "More than microaneurysms but less than severe NPDR (dot/blot hemorrhages, hard exudates).",
    3: "Severe intraretinal hemorrhages (4 quadrants), venous beading (2+ quadrants), or IRMA.",
    4: "Neovascularization of the disc/retina, preretinal or vitreous hemorrhage.",
}

CLINICAL_RECOMMENDATIONS: Dict[int, str] = {
    0: "Routine annual diabetic retinopathy screening.",
    1: "Follow-up screening in 9 to 12 months with primary glycemic control.",
    2: "Comprehensive ophthalmologist consultation within 3 to 6 months.",
    3: "Urgent ophthalmologist evaluation within 2 to 4 weeks.",
    4: "Immediate specialist referral within 24 to 48 hours for clinical intervention.",
}


class ClassProbability(BaseModel):
    """Represents predicted probability for a specific DR severity grade."""
    grade: int = Field(..., ge=0, le=4, description="ICDR Grade (0 to 4)")
    class_name: str = Field(..., description="Severity classification label")
    probability: float = Field(..., ge=0.0, le=1.0, description="Softmax probability value")


class GradCAMResult(BaseModel):
    """Grad-CAM visual explanation output."""
    target_layer: str = Field("conv_head", description="Target convolutional layer analyzed")
    heatmap_min: float = Field(..., description="Minimum raw activation value")
    heatmap_max: float = Field(..., description="Maximum raw activation value")
    heatmap_base64: Optional[str] = Field(None, description="Base64 encoded JPEG/PNG of the blended heatmap overlay")
    overlay_saved_path: Optional[str] = Field(None, description="Filesystem or storage path where overlay was saved")


class PredictionResult(BaseModel):
    """Comprehensive diagnostic inference result."""
    predicted_grade: int = Field(..., ge=0, le=4, description="Most likely DR grade (0-4)")
    severity_label: str = Field(..., description="ICDR severity label")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Top-1 class confidence probability")
    is_referral_recommended: bool = Field(..., description="True if grade >= 2 (Moderate, Severe, or PDR)")
    clinical_recommendation: str = Field(..., description="Clinical triage guidance")
    probabilities: List[ClassProbability] = Field(..., description="Full 5-class probability vector")
    raw_logits: List[float] = Field(..., description="Unnormalized output logits from classifier")
    inference_time_ms: float = Field(..., ge=0.0, description="Inference latency in milliseconds")
    device_used: str = Field(..., description="Compute device utilized (cpu or cuda)")
    model_name: str = Field("efficientnet_b3", description="Model architecture identifier")
    explanation: Optional[GradCAMResult] = Field(None, description="Grad-CAM visual explanation if requested")

