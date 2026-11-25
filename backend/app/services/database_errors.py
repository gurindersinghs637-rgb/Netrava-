"""Translate known transactional PostgreSQL failures without exposing SQL data."""
from fastapi import HTTPException


def raise_known_database_error(exc: Exception) -> None:
    """Raise a stable client error for a recognized SQLSTATE, otherwise return."""
    mapping = {
        "P0002": (404, "RESOURCE_NOT_FOUND", "Resource was not found in this clinic."),
        "42501": (403, "ROLE_FORBIDDEN", "Active authorized clinic membership is required."),
        "55000": (409, "INVALID_STATE", "The operation conflicts with the current record state."),
        "23514": (422, "VALIDATION_ERROR", "The submitted data violates a clinical data constraint."),
        "22P02": (422, "VALIDATION_ERROR", "An identifier or value has an invalid format."),
    }
    entry = mapping.get(getattr(exc, "code", None))
    if entry:
        code, error, message = entry
        raise HTTPException(status_code=code, detail={"error": error, "message": message}) from exc
