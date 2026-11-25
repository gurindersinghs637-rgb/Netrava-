"""
NETRAVA — Screening Routes
============================
POST /api/v1/screenings  — Upload retinal fundus image and run QC
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response

from backend.app.core.security import AuthenticatedUser, get_current_user
from backend.app.ml.image_validator import validate_and_load_image
from backend.app.schemas.screening import (
    ClinicalReportResponse,
    CreateScreeningResponse,
    EyeLateral,
    ReviewRequest,
)
from backend.app.services import report_service, screening_service

router = APIRouter(prefix="/screenings", tags=["Screening"])


@router.post(
    "",
    response_model=CreateScreeningResponse,
    status_code=201,
    summary="Upload retinal fundus image",
    description=(
        "Accepts a retinal fundus image upload (JPEG/PNG, max 15 MB), "
        "runs image quality control, stores it in Supabase Storage, "
        "and returns a signed URL. Requires authentication."
    ),
)
async def create_screening(
    patient_id: str = Form(..., description="Patient UUID."),
    eye: EyeLateral = Form(..., description="Eye laterality: OD (right) or OS (left)."),
    image: UploadFile = File(..., description="Retinal fundus image (JPEG or PNG, max 15 MB)."),
    user: AuthenticatedUser = Depends(get_current_user),
) -> CreateScreeningResponse:
    """Upload a fundus image, run QC assessment, and create a screening session."""
    if user.role not in {"technician", "ophthalmologist", "administrator"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "ROLE_FORBIDDEN", "message": "This role cannot create screenings."})
    pil_image, raw_bytes = await validate_and_load_image(image)

    return await screening_service.create_screening(
        patient_id=patient_id,
        eye=eye,
        image=pil_image,
        raw_bytes=raw_bytes,
        filename=image.filename or "fundus.jpg",
        technician_id=user.id,
        clinic_id=user.clinic_id,
    )


@router.post(
    "/{screening_id}/report",
    response_model=ClinicalReportResponse,
    status_code=200,
    summary="Submit ophthalmologist review",
)
async def submit_report(
    screening_id: str,
    request: ReviewRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> ClinicalReportResponse:
    """Save a clinical review and its audit event for the user's clinic."""
    if user.role not in {"ophthalmologist", "administrator"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "ROLE_FORBIDDEN", "message": "Only an ophthalmologist or clinical administrator can submit a clinical review."},
        )
    return await report_service.submit_review(
        screening_id=screening_id,
        clinic_id=user.clinic_id,
        ophthalmologist_id=user.id,
        request=request,
    )


@router.get(
    "/{screening_id}/report",
    response_model=ClinicalReportResponse,
    summary="Get screening report",
)
async def read_report(
    screening_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> ClinicalReportResponse:
    """Return a report scoped to the authenticated user's clinic."""
    return await report_service.get_report(screening_id=screening_id, clinic_id=user.clinic_id)


@router.get("/{screening_id}/report/pdf", response_class=Response, responses={200: {"content": {"application/pdf": {}}}}, summary="Download clinical report PDF")
async def download_report_pdf(
    screening_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> Response:
    """Download a PDF generated from the caller's persisted clinic report."""
    content = await report_service.get_report_pdf(screening_id, user.clinic_id)
    return Response(content=content, media_type="application/pdf", headers={
        "Content-Disposition": 'attachment; filename="netrava-report.pdf"',
        "Cache-Control": "no-store",
    })



@router.get("/{screening_id}/ai-report/pdf", response_class=Response, responses={200: {"content": {"application/pdf": {}}}}, summary="Generate NETRAVA AI screening report")
async def download_ai_screening_pdf(
    screening_id: UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    prediction_id: UUID | None = None,
) -> Response:
    """Technician-accessible screening support PDF; no clinical privileges granted."""
    content = await report_service.get_ai_screening_pdf(
        str(screening_id), user.clinic_id, str(prediction_id) if prediction_id else None,
    )
    return Response(content=content, media_type="application/pdf", headers={
        "Content-Disposition": 'attachment; filename="netrava-ai-screening.pdf"',
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    })
