"""Generate clinical decision-support PDFs and upload them to private storage."""

from __future__ import annotations

import asyncio
import io
import math
import uuid
from datetime import date, datetime, timezone
from typing import Optional
from xml.sax.saxutils import escape

from fastapi import HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field, field_validator, model_validator
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.app.core.config import settings

_GRADE_LABELS = (
    "No Diabetic Retinopathy",
    "Mild Diabetic Retinopathy",
    "Moderate Diabetic Retinopathy",
    "Severe Diabetic Retinopathy",
    "Proliferative Diabetic Retinopathy",
)
_PRIMARY = colors.HexColor("#075E4D")
_SECONDARY = colors.HexColor("#3C9A78")
_PALE = colors.HexColor("#EAF7F1")
_REPORT_BUCKET = "clinical-reports"
_MAX_HEATMAP_BYTES = 10 * 1024 * 1024
_MAX_PDF_BYTES = 10 * 1024 * 1024


class ReportProbability(BaseModel):
    """One normalized DR probability for grades zero through four."""

    grade: int = Field(ge=0, le=4)
    probability: float = Field(ge=0.0, le=1.0)

    @field_validator("probability")
    @classmethod
    def probability_is_finite(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("Probability must be finite.")
        return value


class ClinicalReportDocument(BaseModel):
    """Only persisted or explicitly supplied values may appear in the PDF."""

    report_id: str = Field(min_length=1, max_length=100)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    clinic_name: Optional[str] = Field(None, max_length=200)
    patient_id: str = Field(min_length=1, max_length=100)
    patient_code: Optional[str] = Field(None, max_length=100)
    patient_name: str = Field(min_length=1, max_length=200)
    date_of_birth: Optional[date] = None
    sex: Optional[str] = Field(None, max_length=40)
    screening_id: str = Field(min_length=1, max_length=100)
    screening_date: Optional[date | datetime] = None
    screening_status: Optional[str] = Field(None, max_length=60)
    retinal_image_ids: list[str] = Field(default_factory=list, max_length=10)
    eye_sides: list[str] = Field(default_factory=list, max_length=10)
    prediction_id: str = Field(min_length=1, max_length=100)
    predicted_grade: int = Field(ge=0, le=4)
    confidence: float = Field(ge=0.0, le=1.0)
    referral_recommended: bool
    probabilities: list[ReportProbability] = Field(max_length=5)
    clinical_assessment: Optional[str] = Field(None, max_length=5000)
    confirmed_grade: Optional[int] = Field(None, ge=0, le=4)
    grade_override: Optional[int] = Field(None, ge=0, le=4)
    urgent_referral: Optional[bool] = None
    signed_off: Optional[bool] = None
    ai_screening: bool = False
    original_png: Optional[bytes] = Field(None, exclude=True)
    gradcam_png: Optional[bytes] = Field(None, exclude=True)

    @field_validator("confidence")
    @classmethod
    def confidence_is_finite(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("Confidence must be finite.")
        return value

    @model_validator(mode="after")
    def validate_prediction_distribution(self) -> "ClinicalReportDocument":
        if self.referral_recommended != (self.predicted_grade >= 2):
            raise ValueError("Referral recommendation must follow the grade >= 2 rule.")
        if self.ai_screening and not self.probabilities:
            return self
        grades = sorted(item.grade for item in self.probabilities)
        if grades != [0, 1, 2, 3, 4]:
            raise ValueError("Exactly one probability is required for each DR grade.")
        total = sum(item.probability for item in self.probabilities)
        if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-3):
            raise ValueError("The five DR probabilities must sum to 1.0.")
        if self.referral_recommended != (self.predicted_grade >= 2):
            raise ValueError("Referral recommendation must follow the grade >= 2 rule.")
        return self


def render_clinical_report_pdf(report: ClinicalReportDocument) -> bytes:
    """Render a validated clinical decision-support report to PDF bytes."""
    output = io.BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=24 * mm,
        bottomMargin=20 * mm,
        title=f"NETRAVA {'AI Screening' if report.ai_screening else 'Clinical'} Report {report.report_id}",
        author="NETRAVA",
        pageCompression=1,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="NetravaTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=18, leading=22, textColor=_PRIMARY, alignment=TA_LEFT, spaceAfter=3 * mm,
    ))
    styles.add(ParagraphStyle(
        name="NetravaSection", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=11, leading=14, textColor=_PRIMARY, spaceBefore=5 * mm, spaceAfter=2 * mm, keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        name="NetravaBody", parent=styles["BodyText"], fontSize=9, leading=12,
        alignment=TA_LEFT, spaceAfter=1.5 * mm,
    ))
    styles.add(ParagraphStyle(
        name="NetravaDisclaimer", parent=styles["BodyText"], fontSize=8,
        leading=10, textColor=colors.HexColor("#3A4A45"),
    ))

    def safe(value: object) -> str:
        return escape(str(value))

    def optional(value: object | None) -> str:
        return safe(value) if value not in (None, "") else "Not recorded"

    story: list[object] = [
        Paragraph("NETRAVA", styles["NetravaTitle"]),
        Paragraph("SEE. DETECT. EXPLAIN.", styles["NetravaBody"]),
        Paragraph("NETRAVA AI Screening Report" if report.ai_screening else "Clinical Screening Report", styles["Heading1"]),
        Paragraph(f"Report ID: {safe(report.report_id)}", styles["NetravaBody"]),
        Paragraph(
            f"Generated on: {report.generated_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            styles["NetravaBody"],
        ),
    ]
    if report.ai_screening:
        story.append(Paragraph(f"Screening date and time: {optional(report.screening_date)}", styles["NetravaBody"]))
    if report.clinic_name:
        story.append(Paragraph(f"Clinic: {safe(report.clinic_name)}", styles["NetravaBody"]))

    patient_rows = [
        ["Patient code", optional(report.patient_code), "Patient ID", safe(report.patient_id)],
        ["Patient name", safe(report.patient_name), "Date of birth", optional(report.date_of_birth)],
        ["Sex", optional(report.sex), "Screening ID", safe(report.screening_id)],
        ["Screening date", optional(report.screening_date), "Status", optional(report.screening_status)],
    ]
    story.extend([
        Paragraph("Patient and screening", styles["NetravaSection"]),
        _key_value_table(patient_rows),
        Paragraph("AI screening result", styles["NetravaSection"]),
    ])

    grade_label = _GRADE_LABELS[report.predicted_grade]
    referral_text = "Ophthalmologist review recommended" if report.referral_recommended else "No referral threshold met"
    result_rows = [
        ["Predicted Diabetic Retinopathy Grade" if report.ai_screening else "Predicted grade", f"{report.predicted_grade} — {grade_label}"],
        ["Confidence", f"{report.confidence:.1%}"],
        ["Referral", referral_text],
        ["Prediction ID", safe(report.prediction_id)],
        ["Retinal image IDs", safe(", ".join(report.retinal_image_ids)) or "Not recorded"],
        ["Eye side(s)", safe(", ".join(report.eye_sides)) or "Not recorded"],
    ]
    story.append(_two_column_table(result_rows))
    story.append(Paragraph("Class probabilities", styles["NetravaSection"]))
    probability_rows = [["Grade", "ICDR category", "Probability"]]
    for item in sorted(report.probabilities, key=lambda entry: entry.grade):
        probability_rows.append([
            str(item.grade), _GRADE_LABELS[item.grade], f"{item.probability:.2%}",
        ])
    if report.probabilities:
        story.append(_probability_table(probability_rows))
    else:
        story.append(Paragraph("Class probabilities were not recorded.", styles["NetravaBody"]))

    if report.confirmed_grade is not None:
        story.extend([
            Paragraph("Clinician review", styles["NetravaSection"]),
            _two_column_table([
                ["Confirmed grade", str(report.confirmed_grade)],
                ["Grade override", optional(report.grade_override)],
                ["Urgent referral", "Yes" if report.urgent_referral else "No"],
                ["Review signed off", "Yes" if report.signed_off else "No"],
            ]),
        ])

    if report.clinical_assessment:
        story.extend([
            Paragraph("Clinical assessment", styles["NetravaSection"]),
            Paragraph(safe(report.clinical_assessment).replace("\n", "<br/>"), styles["NetravaBody"]),
        ])

    if report.ai_screening:
        story.append(Paragraph("Original retinal / fundus image", styles["NetravaSection"]))
        if report.original_png:
            story.append(Image(io.BytesIO(_validated_heatmap(report.original_png)), width=115 * mm, height=80 * mm, kind="proportional"))
        else:
            story.append(Paragraph("Original image unavailable.", styles["NetravaBody"]))
        if not report.gradcam_png:
            story.append(Paragraph("AI Attention / Grad-CAM Visualization: unavailable.", styles["NetravaBody"]))

    if report.gradcam_png:
        heatmap = _validated_heatmap(report.gradcam_png)
        story.extend([
            Paragraph("AI Attention / Grad-CAM Visualization", styles["NetravaSection"]),
            Paragraph("Model attention visualization; this is not a lesion segmentation.", styles["NetravaBody"]),
            Image(io.BytesIO(heatmap), width=115 * mm, height=80 * mm, kind="proportional"),
        ])

    disclaimer = (
        "Clinical decision-support only. This AI output is not a definitive medical diagnosis. "
        "A qualified clinician must review the retinal images and all report findings."
    )
    if report.ai_screening:
        disclaimer = (
            "This result is generated by an AI screening system and is intended to support screening "
            "and clinical decision-making. It is not a final medical diagnosis. A qualified healthcare "
            "professional should review the retinal images and findings before making a diagnosis "
            "or treatment decision."
        )
    story.append(Spacer(1, 5 * mm))
    story.append(KeepTogether([
        Paragraph("IMPORTANT DISCLAIMER" if report.ai_screening else "Clinical disclaimer", styles["NetravaSection"]),
        Paragraph(disclaimer, styles["NetravaDisclaimer"]),
    ]))

    document.build(story, onFirstPage=_draw_page_chrome, onLaterPages=_draw_page_chrome)
    return output.getvalue()


async def upload_report_pdf(
    *, report_id: str, clinic_id: str, pdf_bytes: bytes
) -> tuple[str, str]:
    """Upload a generated PDF to its private bucket and return path plus signed URL."""
    try:
        safe_report_id = str(uuid.UUID(report_id))
        safe_clinic_id = str(uuid.UUID(clinic_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "INVALID_REPORT_REFERENCE", "message": "Report storage reference is invalid."},
        ) from exc
    if (
        not pdf_bytes.startswith(b"%PDF-")
        or len(pdf_bytes) > _MAX_PDF_BYTES
        or not settings.SUPABASE_URL
        or not settings.SUPABASE_SERVICE_ROLE_KEY
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "REPORT_STORAGE_UNAVAILABLE", "message": "Clinical report storage is unavailable."},
        )
    storage_path = f"{safe_clinic_id}/{safe_report_id}/{uuid.uuid4().hex}.pdf"
    client = None
    try:
        from supabase import create_client  # type: ignore

        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        storage = client.storage.from_(_REPORT_BUCKET)
        await asyncio.to_thread(
            storage.upload,
            storage_path,
            pdf_bytes,
            {"content-type": "application/pdf", "upsert": "false"},
        )
        signed = await asyncio.to_thread(storage.create_signed_url, storage_path, 1800)
        signed_url = signed.get("signedURL") or signed.get("signedUrl")
        if not signed_url:
            raise RuntimeError("Storage did not return a signed report URL.")
        return storage_path, str(signed_url)
    except Exception as exc:
        if client is not None:
            try:
                await asyncio.to_thread(client.storage.from_(_REPORT_BUCKET).remove, [storage_path])
            except Exception as cleanup_exc:
                logger.error("Report PDF cleanup failed: {}", type(cleanup_exc).__name__)
        logger.error("Report PDF upload failed: {}", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "REPORT_STORAGE_ERROR", "message": "Clinical report could not be stored."},
        ) from exc


def _key_value_table(rows: list[list[str]]) -> Table:
    styles = [ParagraphStyle("Label", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=_PRIMARY),
              ParagraphStyle("Value", fontName="Helvetica", fontSize=8, leading=10)]
    wrapped = [[Paragraph(value, styles[index % 2]) for index, value in enumerate(row)] for row in rows]
    table = Table(wrapped, colWidths=[29 * mm, 51 * mm, 29 * mm, 51 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), _PALE),
        ("BACKGROUND", (2, 0), (2, -1), _PALE),
        ("TEXTCOLOR", (0, 0), (0, -1), _PRIMARY),
        ("TEXTCOLOR", (2, 0), (2, -1), _PRIMARY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D7E6DF")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _two_column_table(rows: list[list[str]]) -> Table:
    styles = [ParagraphStyle("Label", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=_PRIMARY),
              ParagraphStyle("Value", fontName="Helvetica", fontSize=8.5, leading=11)]
    wrapped = [[Paragraph(value, styles[index]) for index, value in enumerate(row)] for row in rows]
    table = Table(wrapped, colWidths=[43 * mm, 117 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), _PALE),
        ("TEXTCOLOR", (0, 0), (0, -1), _PRIMARY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D7E6DF")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _probability_table(rows: list[list[str]]) -> Table:
    table = Table(rows, colWidths=[20 * mm, 90 * mm, 50 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _PALE]),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D7E6DF")),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _validated_heatmap(value: bytes) -> bytes:
    """Accept only bounded PNG overlays for embedding in a generated report."""
    if len(value) > _MAX_HEATMAP_BYTES:
        raise ValueError("Grad-CAM image exceeds the PDF embedding limit.")
    try:
        with PILImage.open(io.BytesIO(value)) as image:
            if image.format != "PNG" or image.width > 4096 or image.height > 4096:
                raise ValueError("Grad-CAM image must be a bounded PNG.")
            image.verify()
    except Exception as exc:
        raise ValueError("Grad-CAM image is invalid.") from exc
    return value


def _draw_page_chrome(canvas, document) -> None:  # type: ignore[no-untyped-def]
    """Draw a quiet NETRAVA header and page number on each PDF page."""
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(_PRIMARY)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(18 * mm, height - 13 * mm, "NETRAVA")
    canvas.setStrokeColor(_SECONDARY)
    canvas.setLineWidth(1.2)
    canvas.line(18 * mm, height - 16 * mm, width - 18 * mm, height - 16 * mm)
    canvas.setFillColor(colors.HexColor("#53645E"))
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(18 * mm, 11 * mm, "Clinical decision-support report — confidential medical information")
    canvas.drawRightString(width - 18 * mm, 11 * mm, f"Page {document.page}")
    canvas.restoreState()
