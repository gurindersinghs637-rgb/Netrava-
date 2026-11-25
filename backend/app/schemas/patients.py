"""
NETRAVA — Pydantic Schemas: Patients
======================================
Request / response models for patient management endpoints.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


GenderType = Literal["male", "female", "other"]
DiabetesType = Literal["type_1", "type_2", "gestational", "other"]


# ── Requests ─────────────────────────────────────────────────────────────────

class CreatePatientRequest(BaseModel):
    """POST /patients request body."""

    mrn: str = Field(..., min_length=3, max_length=50, description="Medical Record Number — must be unique per clinic.")
    full_name: str = Field(..., min_length=2, max_length=200, description="Patient full name.")
    date_of_birth: date = Field(..., description="Date of birth (YYYY-MM-DD).")
    gender: GenderType = Field(..., description="Biological sex.")
    phone_number: Optional[str] = Field(None, max_length=20, description="Contact phone number.")
    diabetes_type: DiabetesType = Field(..., description="Type of diabetes mellitus.")
    diabetes_duration_years: Optional[int] = Field(None, ge=0, le=100, description="Years since diabetes diagnosis.")
    latest_hba1c: Optional[float] = Field(None, ge=3.0, le=20.0, description="Most recent HbA1c percentage.")
    is_insulin_dependent: bool = Field(False, description="Whether the patient uses insulin.")
    notes: Optional[str] = Field(None, max_length=2000, description="Additional clinical notes.")

    @field_validator("mrn")
    @classmethod
    def mrn_alphanumeric(cls, v: str) -> str:
        import re
        if not re.match(r"^[A-Za-z0-9\-_]+$", v):
            raise ValueError("MRN must contain only letters, digits, hyphens, or underscores.")
        return v.upper()

    @field_validator("full_name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        """Reject whitespace-only names and normalize surrounding spaces."""
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Patient name must contain at least two characters.")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def birth_date_not_future(cls, value: date) -> date:
        """Reject future dates of birth."""
        if value > date.today():
            raise ValueError("Date of birth cannot be in the future.")
        return value


# ── Responses ─────────────────────────────────────────────────────────────────

class PatientSummary(BaseModel):
    """Low-PII patient row matching the existing Supabase patients table."""

    id: str = Field(..., description="Patient UUID.")
    patient_code: str = Field(..., description="Clinic patient identifier.")
    full_name: str
    date_of_birth: Optional[date] = None
    sex: Optional[str] = None
    created_at: Optional[datetime] = None


class PatientDetailResponse(BaseModel):
    """Clinic-scoped patient detail matching the existing live table columns."""

    id: str
    patient_code: str
    full_name: str
    date_of_birth: Optional[date] = None
    sex: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    medical_notes: Optional[str] = None
    clinic_id: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    diabetes_type: Optional[DiabetesType] = None
    diabetes_duration_years: Optional[int] = None
    latest_hba1c: Optional[float] = None
    is_insulin_dependent: bool = False


class CreatePatientResponse(BaseModel):
    """POST /patients response body (201 Created)."""

    id: str
    mrn: str
    full_name: str
    registered_by: str
    clinic_name: Optional[str] = None
    created_at: datetime


class PatientListResponse(BaseModel):
    """GET /patients paginated response body."""

    total: int = Field(..., description="Total matching patients.")
    page: int
    limit: int
    patients: List[PatientSummary]

