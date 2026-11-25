"""Clinical report persistence and retrieval."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import asyncio

from fastapi import HTTPException, status
from loguru import logger

from backend.app.core.config import settings
from backend.app.schemas.screening import ClinicalReportResponse, ReviewRequest
from backend.app.services.database_errors import raise_known_database_error


def _admin_client() -> Any:
    """Create the server-only Supabase client used for report operations."""
    from supabase import create_client  # type: ignore
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def _require_database() -> None:
    """Fail closed when the report database is not configured."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DATABASE_UNAVAILABLE", "message": "Clinical report storage is not configured."},
        )


async def submit_review(
    screening_id: str,
    clinic_id: str,
    ophthalmologist_id: str,
    request: ReviewRequest,
) -> ClinicalReportResponse:
    """Write an ophthalmologist report and immutable audit record atomically."""
    _require_database()
    try:
        client = _admin_client()
        result = client.rpc(
            "write_screening_review",
            {
                "p_screening_id": screening_id,
                "p_clinic_id": clinic_id,
                "p_ophthalmologist_id": ophthalmologist_id,
                "p_overall_grade": request.overall_grade,
                "p_grade_override": request.grade_override,
                "p_ophthalmologist_notes": request.ophthalmologist_notes,
                "p_is_urgent_referral": request.is_urgent_referral,
                "p_is_signed_off": request.is_signed_off,
            },
        ).execute()
        row = result.data
        if isinstance(row, list):
            row = row[0] if row else None
        if not row:
            raise RuntimeError("Report RPC returned no report record.")
        return ClinicalReportResponse.model_validate(row)
    except HTTPException:
        raise
    except Exception as exc:
        raise_known_database_error(exc)
        logger.error("Clinical report save failed: {}", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "REPORT_PERSISTENCE_FAILED", "message": "Clinical report could not be saved."},
        ) from exc


async def get_report(screening_id: str, clinic_id: str) -> ClinicalReportResponse:
    """Fetch a screening report only within the authenticated user's clinic."""
    _require_database()
    try:
        client = _admin_client()
        # Verify screening belongs to clinic_id
        screening_res = client.table("screenings").select("id").eq("id", screening_id).eq("clinic_id", clinic_id).execute()
        if not screening_res.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "REPORT_NOT_FOUND", "message": "Clinical report was not found."})

        result = client.table("reports").select("*").eq("screening_id", screening_id).limit(1).execute()
        if not result.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "REPORT_NOT_FOUND", "message": "Clinical report was not found."})
        row = result.data[0]
        if "is_signed_off" in row:
            return ClinicalReportResponse.model_validate(row)
        if row.get("overall_grade") is None or row.get("is_urgent_referral") is None:
            raise HTTPException(status_code=409, detail={"error": "LEGACY_REPORT_INCOMPLETE", "message": "Historical report requires a clinician review before it can be returned by this API."})
        return ClinicalReportResponse(
            id=row["id"],
            screening_id=row["screening_id"],
            prediction_id=row.get("prediction_id"),
            overall_grade=row["overall_grade"],
            grade_override=row.get("grade_override"),
            ophthalmologist_notes=row.get("clinical_assessment"),
            is_urgent_referral=row["is_urgent_referral"],
            is_signed_off=row.get("review_status") == "approved",
            signed_off_at=datetime.fromisoformat(row["reviewed_at"].replace("Z", "+00:00")) if row.get("reviewed_at") else None,
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Clinical report read failed: {}", type(exc).__name__)
        raise_known_database_error(exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "REPORT_SERVICE_ERROR", "message": "Clinical report could not be retrieved."},
        ) from exc


async def get_report_pdf(screening_id: str, clinic_id: str) -> bytes:
    """Render a report from clinic-authorized persisted data without public URLs."""
    from backend.app.services.report_pdf import ClinicalReportDocument, render_clinical_report_pdf

    report = await get_report(screening_id, clinic_id)
    if not report.prediction_id:
        raise HTTPException(status_code=409, detail={"error": "PREDICTION_REQUIRED", "message": "A persisted prediction is required for PDF generation."})
    try:
        client = _admin_client()
        screening = client.table("screenings").select("id,patient_id,screening_date,status").eq("id", screening_id).eq("clinic_id", clinic_id).execute().data
        if not screening:
            raise HTTPException(status_code=404, detail={"error": "REPORT_NOT_FOUND", "message": "Screening was not found in this clinic."})
        screening = screening[0]
        patients = client.table("patients").select("id,patient_code,full_name,date_of_birth,sex").eq("id", screening["patient_id"]).eq("clinic_id", clinic_id).execute().data
        images = client.table("retinal_images").select("id,eye_side").eq("screening_id", screening_id).execute().data
        predictions = client.table("predictions").select("id,retinal_image_id,predicted_grade,confidence,referral_recommended").eq("id", report.prediction_id).execute().data
        if not patients or not predictions or predictions[0]["retinal_image_id"] not in {row["id"] for row in images}:
            raise HTTPException(status_code=409, detail={"error": "REPORT_DATA_INCOMPLETE", "message": "Report data is incomplete or inconsistent."})
        probabilities = client.table("prediction_probabilities").select("dr_grade,probability").eq("prediction_id", report.prediction_id).execute().data
        patient, prediction = patients[0], predictions[0]
        document = ClinicalReportDocument(
            report_id=report.id, patient_id=patient["id"], patient_code=patient["patient_code"],
            patient_name=patient["full_name"], date_of_birth=patient.get("date_of_birth"), sex=patient.get("sex"),
            screening_id=screening_id, screening_date=screening["screening_date"], screening_status=screening["status"],
            retinal_image_ids=[row["id"] for row in images], eye_sides=[row["eye_side"] for row in images],
            prediction_id=report.prediction_id, predicted_grade=prediction["predicted_grade"], confidence=prediction["confidence"],
            referral_recommended=prediction["referral_recommended"],
            probabilities=[{"grade": row["dr_grade"], "probability": row["probability"]} for row in probabilities],
            clinical_assessment=report.ophthalmologist_notes, confirmed_grade=report.overall_grade,
            grade_override=report.grade_override, urgent_referral=report.is_urgent_referral, signed_off=report.is_signed_off,
        )
        return await asyncio.to_thread(render_clinical_report_pdf, document)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Report PDF generation failed: {}", type(exc).__name__)
        raise HTTPException(status_code=503, detail={"error": "REPORT_PDF_UNAVAILABLE", "message": "Report PDF could not be generated."}) from exc


def _private_report_image(client: Any, row: dict, bucket: str, clinic_id: str) -> bytes | None:
    """Read only an authorized private object; normalize bounded JPEG/PNG for PDF."""
    import io
    from PIL import Image
    path = row.get("storage_path")
    if not path:
        return None
    if row.get("storage_bucket", bucket) != bucket or not path.startswith(f"{clinic_id}/") or any(part in {"..", ".", ""} for part in path.split("/")):
        raise HTTPException(status_code=409, detail={"error": "REPORT_IMAGE_MISMATCH", "message": "Stored image ownership is inconsistent."})
    try:
        raw = client.storage.from_(bucket).download(path)
        if len(raw) > 15 * 1024 * 1024:
            return None
        with Image.open(io.BytesIO(raw)) as image:
            if image.format not in {"JPEG", "PNG"} or image.width * image.height > 25_000_000:
                return None
            image.thumbnail((1600, 1600))
            output = io.BytesIO()
            image.convert("RGB").save(output, format="PNG")
            return output.getvalue()
    except Exception as exc:
        logger.warning("Report image unavailable: {}", type(exc).__name__)
        return None


async def get_ai_screening_pdf(screening_id: str, clinic_id: str, prediction_id: str | None = None) -> bytes:
    """Generate a separate AI support report without creating a clinician review."""
    _require_database()

    def generate() -> bytes:
        from backend.app.services.report_pdf import ClinicalReportDocument, render_clinical_report_pdf
        client = _admin_client()
        screenings = client.table("screenings").select("*").eq("id", screening_id).eq("clinic_id", clinic_id).execute().data
        if not screenings:
            raise HTTPException(status_code=404, detail={"error": "SCREENING_NOT_FOUND", "message": "Screening was not found in your workspace."})
        screening = screenings[0]
        patients = client.table("patients").select("*").eq("id", screening["patient_id"]).eq("clinic_id", clinic_id).execute().data
        images = client.table("retinal_images").select("*").eq("screening_id", screening_id).execute().data
        candidates = []
        for image in images:
            query = client.table("predictions").select("*").eq("retinal_image_id", image["id"])
            if prediction_id:
                query = query.eq("id", prediction_id)
            predictions = query.order("created_at", desc=True).limit(1).execute().data
            candidates.extend((prediction, image) for prediction in predictions)
        if not patients:
            raise HTTPException(status_code=422, detail={"error": "REPORT_DATA_INCOMPLETE", "message": "The screening patient data is missing or inconsistent."})
        if not candidates:
            raise HTTPException(status_code=404, detail={"error": "PREDICTION_NOT_FOUND", "message": "The saved prediction was not found for this screening."})
        prediction, image = max(candidates, key=lambda pair: pair[0]["created_at"])
        patient = patients[0]
        probabilities = client.table("prediction_probabilities").select("dr_grade,probability").eq("prediction_id", prediction["id"]).execute().data
        explanations = client.table("explanations").select("*").eq("prediction_id", prediction["id"]).eq("explanation_type", "Grad-CAM").order("created_at", desc=True).limit(1).execute().data
        document = ClinicalReportDocument(
            ai_screening=True, report_id=f"AI-{prediction['id']}",
            patient_id=patient["id"], patient_code=patient.get("patient_code"), patient_name=patient["full_name"],
            date_of_birth=patient.get("date_of_birth"), sex=patient.get("sex"),
            screening_id=screening_id, screening_date=screening["screening_date"], screening_status=screening.get("status"),
            retinal_image_ids=[image["id"]], eye_sides=[image["eye_side"]],
            prediction_id=prediction["id"], predicted_grade=prediction["predicted_grade"], confidence=prediction["confidence"],
            referral_recommended=prediction["referral_recommended"],
            probabilities=[{"grade": row["dr_grade"], "probability": row["probability"]} for row in probabilities],
            original_png=_private_report_image(client, image, "fundus-images", clinic_id),
            gradcam_png=_private_report_image(client, explanations[0], "gradcam-heatmaps", clinic_id) if explanations else None,
        )
        return render_clinical_report_pdf(document)

    try:
        return await asyncio.to_thread(generate)
    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning("AI screening PDF data invalid: {}", type(exc).__name__)
        raise HTTPException(status_code=422, detail={"error": "REPORT_DATA_INVALID", "message": "The saved screening result contains invalid report data."}) from exc
    except Exception as exc:
        logger.error("AI screening PDF failed: {}", type(exc).__name__)
        raise HTTPException(status_code=500, detail={"error": "REPORT_PDF_UNAVAILABLE", "message": "AI screening PDF could not be generated. Please retry."}) from exc
