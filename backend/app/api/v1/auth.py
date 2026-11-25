"""
NETRAVA — Auth Routes
=======================
POST /api/v1/auth/login   — Authenticate with Supabase GoTrue
GET  /api/v1/auth/me      — Get authenticated user profile
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, Response
from pathlib import Path
from backend.app.schemas.auth import AuthMessage, ForgotPasswordRequest, ResetPasswordRequest
from backend.app.services import password_recovery

from backend.app.core.security import AuthenticatedUser, get_current_user
from backend.app.schemas.auth import LoginRequest, LoginResponse, SignupRequest, SignupResponse, UserProfile
from backend.app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=SignupResponse, status_code=201)
async def signup(request: SignupRequest) -> SignupResponse:
    """Register an active technician in an isolated private workspace."""
    return await auth_service.register_user(request)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=200,
    summary="Sign in to your workspace",
    description=(
        "Authenticates a user with email and password via Supabase GoTrue. "
        "Returns a JWT access token and user profile. No auth required."
    ),
)
async def login(request: LoginRequest) -> LoginResponse:
    """Authenticate a user and return a JWT access token."""
    return await auth_service.authenticate_user(request)


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get current user profile",
    description="Returns the profile of the currently authenticated user.",
)
async def get_me(user: AuthenticatedUser = Depends(get_current_user)) -> UserProfile:
    """Return the authenticated user's profile."""
    return UserProfile(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        clinic_name=user.clinic_name,
    )



@router.post("/forgot-password", response_model=AuthMessage)
async def forgot_password(request: ForgotPasswordRequest) -> AuthMessage:
    """Send a password recovery email without disclosing account existence."""
    return await password_recovery.forgot_password(request)


@router.post("/reset-password", response_model=AuthMessage)
async def reset_password(request: ResetPasswordRequest) -> AuthMessage:
    """Update a password using a one-time Supabase recovery token."""
    return await password_recovery.reset_password(request)


@router.get("/reset-password", response_class=HTMLResponse, include_in_schema=False)
async def reset_password_page() -> HTMLResponse:
    """Serve an isolated reset form; recovery token arrives only in the fragment."""
    return HTMLResponse(
        (Path(__file__).resolve().parents[2] / "templates" / "reset_password.html").read_text(encoding="utf-8"),
        headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer",
                 "X-Content-Type-Options": "nosniff",
                 "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; form-action 'none'; frame-ancestors 'none'"},
    )


@router.get("/reset-password.js", include_in_schema=False)
async def reset_password_script() -> Response:
    """Serve reset logic without inline scripts or third-party resources."""
    return Response((Path(__file__).resolve().parents[2] / "templates" / "reset_password.js").read_text(encoding="utf-8"),
                    media_type="application/javascript", headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})
