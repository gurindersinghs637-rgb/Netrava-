"""
NETRAVA — Pydantic Schemas: Screening & Predictions
=====================================================
Request / response models for screening upload and AI prediction endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

EyeLateral = Literal["OD", "OS"]   # Oculus Dexter / Oculus Sinister


# ── QC Assessment ─────────────────────────────────────────────────────────────

class QCAssessment(BaseModel):
    """Fundus image quality control result."""

    is_gradable: bool = Field(..., description="True if image meets diagnostic quality standards.")
    blur_score: float = Field(..., description="Laplacian variance blur score (higher = sharper).")
    illumination: str = Field(..., description="Illumination quality assessment.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="QC confidence score.")


# ── Screening ─────────────────────────────────────────────────────────────────

class CreateScreeningResponse(BaseModel):
    """POST /screenings response body (201 Created)."""

    screening_id: str
    retinal_image_id: str
    eye: EyeLateral
    qc_assessment: QCAssessment
    fundus_image_signed_url: str = Field(..., description="30-minute signed URL for the stored fundus image.")
    created_at: datetime


# ── AI Prediction ─────────────────────────────────────────────────────────────

class ClassProbabilityResponse(BaseModel):
    """Per-class probability entry in a prediction response."""

    grade: int = Field(..., ge=0, le=4)
    class_name: str
    probability: float = Field(..., ge=0.0, le=1.0)


class GradCAMExplanation(BaseModel):
    """Grad-CAM explainability metadata."""

    target_layer: str = Field(..., description="Model layer used for Grad-CAM (conv_head).")
    heatmap_signed_url: Optional[str] = Field(None, description="30-minute signed URL when the overlay is stored.")
    heatmap_base64: Optional[str] = Field(None, description="Base64 PNG overlay for local or offline inference.")


class PredictRequest(BaseModel):
    """POST /predict request body."""

    retinal_image_id: str = Field(..., description="UUID of the stored retinal image to analyse.")


class PredictResponse(BaseModel):
    """POST /predict response body (200 OK)."""

    prediction_id: Optional[str] = Field(None, description="Database ID; null when persistence is not configured.")
    retinal_image_id: str
    predicted_grade: int = Field(..., ge=0, le=4, description="DR severity grade (0–4).")
    severity_label: str = Field(..., description="Human-readable severity label.")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    is_referral_recommended: bool = Field(
        ...,
        description="True when predicted_grade ≥ 2 (Moderate DR or worse).",
    )
    probabilities: List[ClassProbabilityResponse]
    explanation: GradCAMExplanation
    inference_time_ms: float
    persistence_status: Literal["persisted", "not_configured"]


# ── Clinical Report ────────────────────────────────────────────────────────────

class ReviewRequest(BaseModel):
    """POST /screenings/{id}/review request body."""

    overall_grade: int = Field(..., ge=0, le=4, description="Ophthalmologist's confirmed DR grade.")
    grade_override: Optional[int] = Field(None, ge=0, le=4, description="Override value if different from AI grade.")
    ophthalmologist_notes: Optional[str] = Field(None, max_length=5000)
    is_urgent_referral: bool = Field(False)
    is_signed_off: bool = Field(False, description="Set True to digitally sign the report.")


class ClinicalReportResponse(BaseModel):
    """Persisted ophthalmologist review for a screening."""

    id: str
    screening_id: str
    prediction_id: Optional[str] = None
    overall_grade: int = Field(..., ge=0, le=4)
    grade_override: Optional[int] = Field(None, ge=0, le=4)
    ophthalmologist_notes: Optional[str] = None
    is_urgent_referral: bool
    is_signed_off: bool
    signed_off_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

