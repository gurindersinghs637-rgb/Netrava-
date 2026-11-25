"""
NETRAVA — Pydantic Schemas: Authentication
============================================
Request / response models for auth endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class SignupRequest(BaseModel):
    """Public registration accepts no role, status, or clinic assignment."""

    model_config = ConfigDict(extra="forbid")
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=25)
    password: str = Field(min_length=12, max_length=128, repr=False)
    confirm_password: str = Field(min_length=12, max_length=128, repr=False)

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        """Reject blank names after trimming whitespace."""
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Enter your full name.")
        return value

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, value: str) -> str:
        """Accept common phone punctuation and store normalized digits."""
        import re
        value = value.strip()
        if not re.fullmatch(r"\+?[0-9 ()-]+", value):
            raise ValueError("Enter a valid phone number.")
        digits = re.sub(r"[^0-9]", "", value)
        if not 7 <= len(digits) <= 15:
            raise ValueError("Use 7 to 15 phone digits.")
        return ("+" if value.startswith("+") else "") + digits

    @model_validator(mode="after")
    def matching_passwords(self) -> "SignupRequest":
        """Validate confirmation before contacting the identity provider."""
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class SignupResponse(BaseModel):
    """Registration acknowledgement without tokens or provider metadata."""

    status: Literal["active", "email_confirmation_required"] = "active"
    message: str = "Account created successfully. You can now log in."


# ── Requests ─────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """POST /auth/login request body."""

    email: EmailStr = Field(..., description="User email address.")
    password: str = Field(..., min_length=8, description="Account password.")


# ── Responses ─────────────────────────────────────────────────────────────────

UserRole = Literal["technician", "ophthalmologist", "administrator"]


class UserProfile(BaseModel):
    """Embedded user profile in login and /auth/me responses."""

    id: str = Field(..., description="Supabase user UUID.")
    email: str = Field(..., description="User email address.")
    full_name: str = Field(..., description="Display name.")
    role: UserRole = Field(..., description="RBAC role.")
    clinic_name: Optional[str] = Field(None, description="Affiliated clinic name.")
    created_at: Optional[datetime] = Field(None, description="Account creation timestamp.")


class LoginResponse(BaseModel):
    """POST /auth/login response body."""

    access_token: str = Field(..., description="Short-lived JWT access token.")
    token_type: str = Field("bearer", description="Token type.")
    expires_in: int = Field(..., description="Token lifetime in seconds.")
    user: UserProfile = Field(..., description="Authenticated user profile.")



class ForgotPasswordRequest(BaseModel):
    """Request a recovery email without revealing whether the account exists."""

    model_config = ConfigDict(extra="forbid")
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """One-time recovery proof and matching new password; never persisted locally."""

    model_config = ConfigDict(extra="forbid")
    token_hash: str = Field(min_length=16, max_length=512, repr=False)
    password: str = Field(min_length=12, max_length=128, repr=False)
    confirm_password: str = Field(min_length=12, max_length=128, repr=False)

    @model_validator(mode="after")
    def matching_passwords(self) -> "ResetPasswordRequest":
        """Reject mismatched passwords before consuming the recovery token."""
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class AuthMessage(BaseModel):
    """Public authentication acknowledgement."""

    message: str
