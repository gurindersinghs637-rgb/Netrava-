"""
NETRAVA — AI Prediction Routes
================================
POST /api/v1/predict  — Run EfficientNet-B3 inference + Grad-CAM
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from backend.app.core.security import AuthenticatedUser, get_current_user
from backend.app.ml.image_validator import validate_and_load_image
from backend.app.schemas.screening import PredictResponse
from backend.app.services import prediction_service

router = APIRouter(prefix="/predict", tags=["AI Prediction"])


@router.post(
    "",
    response_model=PredictResponse,
    status_code=200,
    summary="Run AI inference on a retinal image",
    description=(
        "Accepts a retinal image file directly, runs EfficientNet-B3 classification, "
        "generates Grad-CAM explainability heatmap, and returns the prediction with "
        "5-class probabilities and a Grad-CAM overlay signed URL. "
        "Requires technician or ophthalmologist role."
    ),
)
async def predict(
    retinal_image_id: str,
    image: UploadFile = File(..., description="Retinal fundus image (JPEG or PNG)."),
    user: AuthenticatedUser = Depends(get_current_user),
) -> PredictResponse:
    """Run AI inference and Grad-CAM on a submitted retinal image."""
    if user.role not in {"technician", "ophthalmologist", "administrator"}:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "ROLE_FORBIDDEN", "message": "This role cannot request predictions."})
    pil_image, raw_bytes = await validate_and_load_image(image)

    return await prediction_service.run_prediction(
        retinal_image_id=retinal_image_id,
        image=pil_image,
        raw_bytes=raw_bytes,
        requested_by=user.id,
        clinic_id=user.clinic_id,
    )

