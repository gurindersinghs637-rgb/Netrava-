"""
NETRAVA — JWT Security Utilities
==================================
Provides token verification and dependency helpers for FastAPI route protection.

Design rules (from AGENT.md and docs/SECURITY.md):
- Use HS256 with SECRET_KEY for token verification.
- Raise HTTP 401 with a structured error body on any failure.
- Never log or return raw token strings.
- All public functions are type-annotated.
"""

from __future__ import annotations

from typing import Literal, Optional

import httpx
from pydantic import BaseModel

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from loguru import logger

from backend.app.core.config import settings
from backend.app.services.auth_service import fetch_active_profile

# Bearer token extractor — auto 403 when header missing is disabled so we can
# return a clean 401 instead.
_bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Enter your Supabase JWT access token. (If pasting directly into Swagger UI, do not type 'Bearer ', just paste the raw token).",
)

# ── Constants ────────────────────────────────────────────────────────────────
ALGORITHM = "HS256"


# ── Low-level helpers ────────────────────────────────────────────────────────

def verify_jwt_token(token: str) -> dict:
    """Decode and verify a JWT token string.

    Args:
        token: Raw JWT string (without "Bearer " prefix).

    Returns:
        Decoded payload dictionary.

    Raises:
        HTTPException 401: If the token is missing, expired, or invalid.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "MISSING_TOKEN", "message": "Authentication token is required."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not settings.is_testing:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "INVALID_TOKEN", "message": "Locally signed test tokens are disabled."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload: dict = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return payload

    except ExpiredSignatureError:
        logger.warning("JWT token has expired.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "TOKEN_EXPIRED", "message": "Authentication token has expired."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as exc:
        logger.warning(f"JWT decode error: {type(exc).__name__}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "INVALID_TOKEN", "message": "Authentication token is invalid."},
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_id(token: str) -> str:
    """Extract the user ID (``sub`` claim) from a verified JWT.

    Args:
        token: Raw JWT string.

    Returns:
        User ID string from the ``sub`` claim.

    Raises:
        HTTPException 401: If the token is invalid or ``sub`` is missing.
    """
    payload = verify_jwt_token(token)
    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "INVALID_TOKEN_PAYLOAD", "message": "Token is missing subject claim."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


# ── FastAPI dependency ────────────────────────────────────────────────────────

class AuthenticatedUser(BaseModel):
    """Trusted server-side identity and clinic membership for a request."""

    id: str
    email: str = ""
    full_name: str = ""
    role: Literal["technician", "ophthalmologist", "administrator"]
    clinic_id: str
    clinic_name: Optional[str] = None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> AuthenticatedUser:
    """Verify a Supabase access token and load trusted role/clinic membership.

    Returns:
        Authenticated user identity with database-backed role and clinic.

    Raises:
        HTTPException 401: On any authentication failure.

    Usage::

        @router.get("/protected")
        async def protected_route(user_id: str = Depends(get_current_user)):
            ...
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "MISSING_TOKEN", "message": "Authentication token is required."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Sanitize token to tolerate leading/trailing spaces, quotes, or redundant "Bearer " prefix (e.g. from Swagger UI paste)
    raw_token = credentials.credentials.strip()
    if raw_token.lower().startswith("bearer "):
        raw_token = raw_token[7:].strip()
    raw_token = raw_token.strip("\"'")

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "MISSING_TOKEN", "message": "Authentication token is required."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    if settings.is_testing:
        payload = verify_jwt_token(raw_token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "INVALID_TOKEN", "message": "Token subject is missing."})
        return AuthenticatedUser(
            id=str(user_id),
            role="technician",
            clinic_id="00000000-0000-0000-0000-000000000001",
            clinic_name="Test Clinic",
        )

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "AUTH_UNAVAILABLE", "message": "Trusted authentication is not configured."},
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            auth_response = await client.get(
                f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user",
                headers={
                    "apikey": settings.SUPABASE_KEY,
                    "Authorization": f"Bearer {raw_token}",
                },
            )
            if auth_response.status_code != 200:
                if auth_response.status_code not in {400, 401, 403}:
                    auth_response.raise_for_status()
                logger.warning(
                    "Supabase token verification failed | status={}",
                    auth_response.status_code,
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "INVALID_TOKEN",
                    "message": "Authentication token is invalid or expired.",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
            identity = auth_response.json()
            user_id = str(identity.get("id", ""))
            if not user_id:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "INVALID_TOKEN", "message": "Authentication identity is missing."})

            profile = await fetch_active_profile(
                user_id=user_id,
                url=settings.SUPABASE_URL.rstrip("/"),
                service_key=settings.SUPABASE_SERVICE_ROLE_KEY,
            )
            role = profile.get("role")
            clinic_id = profile.get("clinic_id")
            if role not in {"technician", "ophthalmologist", "administrator"} or not clinic_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "PROFILE_INVALID", "message": "Your workspace access could not be verified. Please contact support."})
            return AuthenticatedUser(
                id=user_id,
                email=str(identity.get("email") or ""),
                full_name=str(profile.get("full_name") or ""),
                role=role,
                clinic_id=str(clinic_id),
                clinic_name=(profile.get("clinic") or {}).get("clinic_name"),
            )
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
        logger.error("Authentication provider request failed: {}", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "AUTH_SERVICE_ERROR", "message": "Authentication service is unavailable."},
        ) from exc

