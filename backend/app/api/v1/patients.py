"""
NETRAVA — Patient Routes
==========================
POST /api/v1/patients    — Register a new patient
GET  /api/v1/patients    — Paginated patient list
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.app.core.security import AuthenticatedUser, get_current_user
from backend.app.schemas.patients import (
    CreatePatientRequest,
    CreatePatientResponse,
    PatientDetailResponse,
    PatientListResponse,
)
from backend.app.services import patient_service

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post(
    "",
    response_model=CreatePatientResponse,
    status_code=201,
    summary="Register a new patient",
    description="Creates a new diabetic patient record. Requires technician or ophthalmologist role.",
)
async def create_patient(
    request: CreatePatientRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> CreatePatientResponse:
    """Register a new patient in the clinic registry."""
    if user.role not in {"technician", "ophthalmologist", "administrator"}:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "ROLE_FORBIDDEN", "message": "This role cannot register patients."})
    return await patient_service.create_patient(
        request=request,
        registered_by=user.id,
        clinic_id=user.clinic_id,
    )


@router.get(
    "",
    response_model=PatientListResponse,
    summary="List patients",
    description="Paginated and searchable list of clinic patients.",
)
async def list_patients(
    search: Optional[str] = Query(None, description="Search by patient name or patient code."),
    page: int = Query(1, ge=1, description="Page number (1-based)."),
    limit: int = Query(20, ge=1, le=100, description="Records per page (max 100)."),
    user: AuthenticatedUser = Depends(get_current_user),
) -> PatientListResponse:
    """Return a paginated list of patients matching the search query."""
    return await patient_service.list_patients(
        page=page,
        limit=limit,
        search=search,
        clinic_id=user.clinic_id,
    )


@router.get(
    "/{patient_id}",
    response_model=PatientDetailResponse,
    summary="Get patient details",
    description="Returns patient details only when the patient belongs to the authenticated user's clinic.",
)
async def get_patient(
    patient_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> PatientDetailResponse:
    """Return one clinic-scoped patient detail record."""
    return await patient_service.get_patient(patient_id=patient_id, clinic_id=user.clinic_id)

