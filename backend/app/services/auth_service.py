"""Supabase GoTrue authentication and trusted user profile access."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException, status
from loguru import logger

from backend.app.core.config import settings
from backend.app.schemas.auth import LoginRequest, LoginResponse, SignupRequest, SignupResponse, UserProfile


_SIGNUP_ERROR_CODES = {
    "user_already_exists", "email_exists", "weak_password", "email_address_invalid",
    "email_address_not_authorized", "signup_disabled", "over_email_send_rate_limit",
    "over_request_rate_limit", "unexpected_failure", "email_send_failed",
    "request_timeout", "hook_timeout", "hook_timeout_after_retry", "hook_payload_invalid_content_type",
}


def _log_signup_failure(stage: str, response: httpx.Response) -> None:
    """Log only fixed stage names, status and recognized provider codes, never bodies."""
    try:
        body = response.json()
        code = (body.get("error_code") or body.get("code")) if isinstance(body, dict) else None
    except ValueError:
        body = {}
        code = None
    safe_code = code if isinstance(code, str) and code in _SIGNUP_ERROR_CODES else "unrecognized"
    message = str(body.get("msg") or body.get("message") or "").lower() if isinstance(body, dict) else ""
    if code == "email_send_failed" or message in {"error sending confirmation email", "error sending confirmation mail"}:
        category = "email_delivery"
    elif message == "database error saving new user":
        category = "database_setup"
    else:
        category = "provider_failure"
    logger.error("Supabase signup failed: stage={} status={} provider_code={} category={}", stage, response.status_code, safe_code, category)


async def register_user(request: SignupRequest) -> SignupResponse:
    """Use GoTrue signup and verify the atomic active private-workspace profile."""
    url, public_key, service_key = _require_supabase()
    stage = "duplicate_check"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # GoTrue may conceal duplicate confirmed users, or re-send confirmation
            # for unconfirmed users. Check trusted identities before attempting signup.
            page = 1
            while True:
                existing = await client.get(
                    f"{url}/auth/v1/admin/users",
                    params={"page": page, "per_page": 100},
                    headers={"apikey": service_key, "Authorization": f"Bearer {service_key}"},
                )
                existing.raise_for_status()
                users = existing.json().get("users", [])
                if any(str(user.get("email", "")).lower() == str(request.email).lower() for user in users):
                    raise HTTPException(409, detail={"error": "EMAIL_EXISTS", "message": "This email is already registered. Please log in with your existing password or use Forgot Password to reset it."})
                if len(users) < 100:
                    break
                page += 1
            stage = "signup"
            response = await client.post(
                f"{url}/auth/v1/signup",
                headers={"apikey": public_key},
                json={"email": str(request.email), "password": request.password,
                      "data": {"full_name": request.full_name, "phone": request.phone}},
            )
            body = response.json()
            if response.is_error:
                _log_signup_failure(stage, response)
            code = body.get("error_code") or body.get("code")
            # Older GoTrue versions return only a message for duplicate accounts.
            provider_message = str(body.get("msg") or body.get("message") or "").lower()
            if code in {"user_already_exists", "email_exists"} or provider_message in {"user already registered", "a user with this email address has already been registered"}:
                raise HTTPException(409, detail={"error": "EMAIL_EXISTS", "message": "This email is already registered. Please log in with your existing password or use Forgot Password to reset it."})
            if response.is_error and (code == "email_send_failed" or provider_message in {"error sending confirmation email", "error sending confirmation mail"}):
                raise HTTPException(503, detail={"error": "SIGNUP_EMAIL_DELIVERY_FAILED", "message": "The authentication service could not send your confirmation email. Please contact support before registering again."})
            if response.is_error and provider_message == "database error saving new user":
                raise HTTPException(503, detail={"error": "SIGNUP_DATABASE_ERROR", "message": "Account workspace setup failed in the authentication service. Please contact support before registering again."})
            if response.is_error and code in {"request_timeout", "hook_timeout", "hook_timeout_after_retry"}:
                raise HTTPException(503, detail={"error": "SIGNUP_PROVIDER_TIMEOUT", "message": "Registration timed out at the authentication service. Please contact support to check whether your account was created before retrying."})
            if response.is_error and code == "over_email_send_rate_limit":
                raise HTTPException(429, detail={"error": "EMAIL_RATE_LIMITED", "message": "Too many confirmation emails requested. Please wait before trying again."})
            if response.status_code == 429:
                raise HTTPException(429, detail={"error": "SIGNUP_RATE_LIMITED", "message": "Too many attempts. Please try again later."})
            if response.status_code in {400, 403, 422}:
                known_errors = {
                    "weak_password": ("WEAK_PASSWORD", "Use at least 12 characters for your NETRAVA password."),
                    "email_address_invalid": ("INVALID_EMAIL", "Enter a valid email address."),
                    "email_address_not_authorized": ("EMAIL_DELIVERY_RESTRICTED", "Email delivery is restricted by the authentication provider. Please contact support."),
                    "signup_disabled": ("SIGNUP_DISABLED", "New account registration is currently disabled. Please contact support."),
                    "over_email_send_rate_limit": ("EMAIL_RATE_LIMITED", "Too many confirmation emails requested. Please wait before trying again."),
                }
                if code in known_errors:
                    error, message = known_errors[code]
                    raise HTTPException(400, detail={"error": error, "message": message})
                raise HTTPException(400, detail={"error": "SIGNUP_REJECTED", "message": "Registration was rejected. Check your email and password and try again."})
            response.raise_for_status()
            identity = body.get("user") or body
            # GoTrue can conceal a duplicate email behind an obfuscated user.
            if identity.get("identities") == []:
                raise HTTPException(409, detail={"error": "EMAIL_EXISTS", "message": "This email is already registered. Please log in with your existing password or use Forgot Password to reset it."})
            if not identity.get("id"):
                raise ValueError("Missing registration identity")
            stage = "profile_verification"
            profile_response = await client.get(
                f"{url}/rest/v1/user_profiles",
                params={"id": f"eq.{identity['id']}", "select": "id,full_name,email,phone,role,clinic_id,is_active"},
                headers={"apikey": service_key, "Authorization": f"Bearer {service_key}"},
            )
            profile_response.raise_for_status()
            profiles = profile_response.json()
            if not profiles or profiles[0].get("role") != "technician" or profiles[0].get("is_active") is not True or not profiles[0].get("clinic_id") or profiles[0].get("phone") != request.phone or profiles[0].get("email") != str(request.email):
                raise ValueError("Active profile trigger missing or unsafe")
        if not body.get("access_token") and not identity.get("email_confirmed_at"):
            return SignupResponse(status="email_confirmation_required", message="Account created. Confirm your email, then log in to your private workspace.")
        return SignupResponse()
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        # Signup errors have already been logged before interpreting the response.
        if stage != "signup":
            _log_signup_failure(stage, exc.response)
        raise HTTPException(503, detail={"error": "SIGNUP_UNAVAILABLE", "message": "Registration could not be verified. Please contact support before retrying."}) from exc
    except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
        logger.error("Supabase signup failed: stage={} exception={}", stage, type(exc).__name__)
        raise HTTPException(503, detail={"error": "SIGNUP_UNAVAILABLE", "message": "Registration could not be verified. Please contact support before retrying."}) from exc


def _require_supabase() -> tuple[str, str, str]:
    """Return configured Supabase URL, public key, and backend service key."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "AUTH_UNAVAILABLE", "message": "Authentication service is not configured."},
        )
    return settings.SUPABASE_URL.rstrip("/"), settings.SUPABASE_KEY, settings.SUPABASE_SERVICE_ROLE_KEY


async def fetch_active_profile(user_id: str, url: str, service_key: str) -> dict[str, Any]:
    """Fetch trusted app role and clinic membership from user_profiles."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{url}/rest/v1/user_profiles",
            params={
                "id": f"eq.{user_id}",
                "select": "id,role,clinic_id,full_name,is_active,clinic:clinics(clinic_name,is_active)",
            },
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
            },
        )
        response.raise_for_status()
    profiles = response.json()
    if not profiles or profiles[0].get("is_active") is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "ACCOUNT_DISABLED", "message": "Account has been disabled."},
        )
    profile = profiles[0]
    if not profile.get("clinic") or profile["clinic"].get("is_active") is not True:
        raise HTTPException(status_code=403, detail={"error": "CLINIC_DISABLED", "message": "Your workspace is unavailable. Please contact support."})
    if profile.get("role") not in {"technician", "ophthalmologist", "administrator"} or not profile.get("clinic_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "PROFILE_INVALID", "message": "Your workspace access could not be verified. Please contact support."},
        )
    return profile


def _to_profile(identity: dict[str, Any], profile: dict[str, Any]) -> UserProfile:
    """Build the public profile using trusted database role and clinic data."""
    return UserProfile(
        id=str(identity["id"]),
        email=str(identity.get("email") or ""),
        full_name=str(profile.get("full_name") or ""),
        role=profile["role"],
        clinic_name=(profile.get("clinic") or {}).get("clinic_name"),
    )


async def authenticate_user(request: LoginRequest) -> LoginResponse:
    """Authenticate through GoTrue and require an active database profile."""
    url, public_key, service_key = _require_supabase()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{url}/auth/v1/token?grant_type=password",
                headers={"apikey": public_key, "Content-Type": "application/json"},
                json={"email": request.email, "password": request.password},
            )
        if response.status_code in {400, 401}:
            try:
                failure = response.json()
            except ValueError:
                failure = {}
            if isinstance(failure, dict) and (failure.get("error_code") or failure.get("code")) == "email_not_confirmed":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"error": "EMAIL_NOT_CONFIRMED", "message": "Please confirm your email using the registration email before logging in. If the email did not arrive, contact support."},
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "INVALID_CREDENTIALS", "message": "Email or password is incorrect."},
            )
        response.raise_for_status()
        session = response.json()
        identity = session.get("user") or {}
        if not session.get("access_token") or not identity.get("id"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "INVALID_CREDENTIALS", "message": "Email or password is incorrect."})
        profile = await fetch_active_profile(str(identity["id"]), url, service_key)
        return LoginResponse(
            access_token=session["access_token"],
            token_type="bearer",
            expires_in=int(session.get("expires_in") or 3600),
            user=_to_profile(identity, profile),
        )
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
        logger.error("Supabase login request failed: {}", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "AUTH_SERVICE_ERROR", "message": "Authentication service is unavailable."},
        ) from exc


async def get_user_profile(user_id: str) -> UserProfile:
    """Fetch an active trusted profile for a verified Supabase user ID."""
    url, _, service_key = _require_supabase()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{url}/auth/v1/admin/users/{user_id}",
                headers={"apikey": service_key, "Authorization": f"Bearer {service_key}"},
            )
            if response.status_code == 404:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "USER_NOT_FOUND", "message": "User profile not found."})
            response.raise_for_status()
            identity = response.json()
        profile = await fetch_active_profile(user_id, url, service_key)
        return _to_profile(identity, profile)
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        logger.error("Supabase profile request failed: {}", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "AUTH_SERVICE_ERROR", "message": "Could not retrieve the user profile."},
        ) from exc
