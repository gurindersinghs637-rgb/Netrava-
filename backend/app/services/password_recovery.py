"""Supabase one-time recovery; never changes profile data or handles admin resets."""
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException

from backend.app.core.config import settings
from backend.app.schemas.auth import AuthMessage, ForgotPasswordRequest, ResetPasswordRequest
from backend.app.services.auth_service import _require_supabase


async def forgot_password(request: ForgotPasswordRequest) -> AuthMessage:
    """Ask GoTrue to deliver recovery instructions using a fixed trusted URL."""
    url, public_key, _ = _require_supabase()
    redirect = settings.PASSWORD_RESET_REDIRECT_URL
    parsed = urlparse(redirect)
    if not parsed.netloc or (parsed.scheme != "https" and not (
        settings.ENVIRONMENT == "development" and parsed.scheme == "http"
    )) or parsed.fragment or parsed.query:
        raise HTTPException(503, detail={"error": "RECOVERY_NOT_CONFIGURED", "message": "Password recovery is not configured. Please contact support."})
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                url + "/auth/v1/recover", params={"redirect_to": redirect},
                headers={"apikey": public_key}, json={"email": str(request.email)},
            )
            if response.status_code == 429:
                raise HTTPException(429, detail={"error": "RECOVERY_RATE_LIMITED", "message": "Too many requests. Please wait before trying again."})
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(503, detail={"error": "RECOVERY_UNAVAILABLE", "message": "Recovery email could not be requested. Please try again later."}) from exc
    return AuthMessage(message="If an account exists for this email, you will receive a password reset link. Check your inbox and spam folder.")


async def reset_password(request: ResetPasswordRequest) -> AuthMessage:
    """Exchange recovery-only proof and update the password through GoTrue."""
    url, public_key, _ = _require_supabase()
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            verification = await client.post(
                url + "/auth/v1/verify", headers={"apikey": public_key},
                json={"token_hash": request.token_hash, "type": "recovery"},
            )
            if verification.status_code in {400, 401, 403, 404, 422}:
                raise HTTPException(400, detail={"error": "INVALID_RECOVERY_LINK", "message": "This reset link is invalid or expired. Request a new link."})
            verification.raise_for_status()
            token = verification.json().get("access_token")
            if not token:
                raise ValueError("Missing recovery session")
            response = await client.put(
                url + "/auth/v1/user",
                headers={"apikey": public_key, "Authorization": "Bearer " + token},
                json={"password": request.password},
            )
            if response.status_code in {400, 422}:
                raise HTTPException(400, detail={"error": "PASSWORD_REJECTED", "message": "Use at least 12 characters and a password different from your current password. Request a new reset link to try again."})
            response.raise_for_status()
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        raise HTTPException(503, detail={"error": "RESET_UNAVAILABLE", "message": "Password reset could not be completed. Try logging in before requesting another link."}) from exc
    return AuthMessage(message="Password updated. Return to NETRAVA and log in with your new password.")
