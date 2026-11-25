"""
NETRAVA — Patient Service
==========================
Business logic for patient registration and retrieval.

Design rules:
- All Supabase queries use the service role key (backend only).
- Never expose service_role key in responses.
- Duplicate MRN raises 409 Conflict.
- All functions are async and type-annotated.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from loguru import logger

from backend.app.core.config import settings
from backend.app.services.database_errors import raise_known_database_error
from backend.app.schemas.patients import (
    CreatePatientRequest,
    CreatePatientResponse,
    PatientDetailResponse,
    PatientListResponse,
    PatientSummary,
)


def _get_admin_client() -> Any:
    """Return a Supabase client with service role key."""
    from supabase import create_client  # type: ignore
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def _sanitize_search(search: str) -> str:
    """Keep ordinary name/MRN characters and strip PostgREST filter syntax."""
    return "".join(char for char in search if char.isalnum() or char in " _-")[:100].strip()


async def create_patient(
    request: CreatePatientRequest,
    registered_by: str,
    clinic_id: str,
) -> CreatePatientResponse:
    """Register a new patient in the database.

    Args:
        request: Validated patient intake form data.
        registered_by: UUID of the authenticated technician / ophthalmologist.
        clinic_id: Trusted clinic identifier from the authenticated profile.

    Returns:
        CreatePatientResponse with the new patient record.

    Raises:
        HTTPException 409: MRN already exists.
        HTTPException 503: Database unavailable.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DATABASE_UNAVAILABLE", "message": "Database service is not configured."},
        )

    try:
        payload: Dict[str, Any] = {
            "mrn": request.mrn,
            "full_name": request.full_name,
            "date_of_birth": str(request.date_of_birth),
            "gender": request.gender,
            "phone_number": request.phone_number,
            "diabetes_type": request.diabetes_type,
            "diabetes_duration_years": request.diabetes_duration_years,
            "latest_hba1c": request.latest_hba1c,
            "is_insulin_dependent": request.is_insulin_dependent,
            "notes": request.notes,
            "registered_by": registered_by,
            "clinic_id": clinic_id,
        }

        client = _get_admin_client()
        result = client.rpc("register_clinic_patient", {"p_patient": payload}).execute()
        row = result.data
        if isinstance(row, list):
            row = row[0] if row else None
        if not row:
            raise RuntimeError("Patient registration RPC returned no row.")

        logger.info("Patient record created.")
        created_at_val = row["created_at"]
        if isinstance(created_at_val, str):
            created_at_dt = datetime.fromisoformat(created_at_val.replace("Z", "+00:00"))
        else:
            created_at_dt = created_at_val

        return CreatePatientResponse(
            id=row["id"],
            mrn=row.get("mrn") or row.get("patient_code"),
            full_name=row["full_name"],
            registered_by=str(row.get("registered_by") or row.get("created_by") or registered_by),
            clinic_name=row.get("clinic_name"),
            created_at=created_at_dt,
        )

    except HTTPException:
        raise
    except Exception as exc:
        if getattr(exc, "code", None) == "23505":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "MRN_ALREADY_EXISTS", "message": "A patient with this MRN already exists in the clinic."},
            ) from exc
        logger.error("Patient create failed: {}", type(exc).__name__)
        raise_known_database_error(exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DATABASE_ERROR", "message": "Could not register the patient."},
        ) from exc


async def list_patients(
    clinic_id: str,
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
) -> PatientListResponse:
    """Return a paginated list of patients.

    Args:
        page: 1-based page number.
        limit: Records per page (max 100).
        search: Optional free-text filter on full_name or patient_code.
        clinic_id: Trusted clinic identifier from the authenticated profile.

    Returns:
        PatientListResponse with total count and patient list.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DATABASE_UNAVAILABLE", "message": "Database service is not configured."},
        )

    limit = min(limit, 100)
    offset = (page - 1) * limit

    try:
        client = _get_admin_client()
        query = (
            client.table("patients")
            .select("id,patient_code,full_name,date_of_birth,sex,created_at", count="exact")
            .eq("clinic_id", clinic_id)
        )
        if search:
            safe_search = _sanitize_search(search)
            if safe_search:
                # Filter grammar characters are removed before using PostgREST's OR syntax.
                query = query.or_(
                    f"full_name.ilike.%{safe_search}%,patient_code.ilike.%{safe_search}%"
                )

        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

        patients: List[PatientSummary] = [
            PatientSummary(**{k: v for k, v in row.items() if k in PatientSummary.model_fields})
            for row in (result.data or [])
        ]

        return PatientListResponse(
            total=result.count or 0,
            page=page,
            limit=limit,
            patients=patients,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Patient list failed: {}", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DATABASE_ERROR", "message": "Could not retrieve patient list."},
        ) from exc


async def get_patient(patient_id: str, clinic_id: str) -> PatientDetailResponse:
    """Retrieve one patient only when its trusted clinic ID matches the caller."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DATABASE_UNAVAILABLE", "message": "Database service is not configured."},
        )
    try:
        result = (
            _get_admin_client()
            .table("patients")
            .select(
                "id,patient_code,full_name,date_of_birth,sex,phone,email,medical_notes,"
                "clinic_id,created_by,created_at,updated_at,diabetes_type,"
                "diabetes_duration_years,latest_hba1c,is_insulin_dependent"
            )
            .eq("id", patient_id)
            .eq("clinic_id", clinic_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PATIENT_NOT_FOUND", "message": "Patient was not found in this clinic."},
            )
        return PatientDetailResponse.model_validate(result.data[0])
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Patient detail read failed: {}", type(exc).__name__)
        raise_known_database_error(exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DATABASE_ERROR", "message": "Could not retrieve patient details."},
        ) from exc

