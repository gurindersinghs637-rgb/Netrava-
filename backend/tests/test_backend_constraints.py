"""Stable client failures for validation, database constraints and storage outages."""
from datetime import date, timedelta
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from backend.app.schemas.patients import CreatePatientRequest
from backend.app.services.database_errors import raise_known_database_error


@pytest.mark.parametrize("sqlstate,status", [("P0002",404),("42501",403),("55000",409),("23514",422),("22P02",422)])
def test_database_constraint_errors_do_not_leak_sql(sqlstate, status):
    """Translate recognized SQLSTATEs without copying SQL text into responses."""
    error = RuntimeError("SENSITIVE_SQL_VALUE")
    error.code = sqlstate
    with pytest.raises(HTTPException) as result:
        raise_known_database_error(error)
    assert result.value.status_code == status
    assert "SENSITIVE_SQL_VALUE" not in str(result.value.detail)


@pytest.mark.parametrize("change", [{"full_name":"  "}, {"date_of_birth":date.today()+timedelta(days=1)}])
def test_patient_rejects_blank_name_and_future_birth(change):
    """Invalid demographics fail before any database write."""
    data = dict(mrn="TEST-001",full_name="Synthetic Patient",date_of_birth=date(1980,1,1),gender="female",diabetes_type="type_2")
    with pytest.raises(ValidationError):
        CreatePatientRequest(**{**data,**change})


@pytest.mark.asyncio
async def test_gradcam_storage_failure_never_silently_succeeds(monkeypatch):
    """Configured explanation persistence is mandatory for successful inference."""
    import supabase
    from backend.app.core.config import settings
    from backend.app.services.prediction_service import _upload_gradcam
    monkeypatch.setattr(settings,"SUPABASE_URL","https://example.invalid")
    monkeypatch.setattr(settings,"SUPABASE_SERVICE_ROLE_KEY","controlled-key")
    def unavailable(*_args):
        raise RuntimeError("SENSITIVE_STORAGE_DETAIL")
    monkeypatch.setattr(supabase,"create_client",unavailable)
    with pytest.raises(HTTPException) as result:
        await _upload_gradcam(b"image","image","clinic")
    assert result.value.status_code == 503
    assert "SENSITIVE_STORAGE_DETAIL" not in str(result.value.detail)
