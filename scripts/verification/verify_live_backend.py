"""Operator-run live workflow; passwords are prompted privately and never stored.

Run from the project root after applying the normalized migration. This creates
clearly marked demonstration records and audit events, which are retained.
"""
from __future__ import annotations

import getpass
import logging
import sys
import uuid
import argparse
import asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings
from scripts.verification.retinal_fixture import prepare_verification_image


class VerificationFailure(RuntimeError):
    """A failure label safe to display without response bodies or credentials."""


def main() -> int:
    """Check live login, clinic membership and the full persisted demo workflow."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, help="Custom retinal image, checked unchanged at its supplied resolution.")
    parser.add_argument("--check-fixture", action="store_true", help="Run production image validation/QC locally, without credentials or network.")
    parser.add_argument("--ai-report", action="store_true", help="Verify technician AI screening PDF without creating a clinician review.")
    parser.add_argument("--pdf-output", type=Path, default=ROOT / "tmp" / "netrava-live-report.pdf", help="Private local output for manual PDF inspection; do not commit it.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    selected_path = args.image
    if not args.check_fixture and selected_path is None:
        entered = input("Retinal image path [blank = bundled retinal fixture at 400px]: ").strip()
        selected_path = Path(entered) if entered else None
    try:
        raw, media, qc = asyncio.run(prepare_verification_image(selected_path))
    except Exception:
        logging.error("Image preflight failed: select a readable JPEG/PNG that passes production QC. No login or database writes were attempted.")
        return 1
    logging.warning("PASS production image preflight: blur_score=%.2f, illumination=%s; source=%s", qc.blur_score, qc.illumination, "custom unchanged" if selected_path else "bundled retina, fixed 400px resize")
    if args.check_fixture:
        return 0
    if settings.is_testing:
        logging.error("Use development configuration for live verification.")
        return 1
    logging.getLogger("httpx").setLevel(logging.WARNING)
    account_label = "authorized technician/clinician" if args.ai_report else "ophthalmologist/administrator"
    email = input(f"Existing {account_label} test email (kept local): ").strip()
    password = getpass.getpass("Password (hidden): ")
    other_email = input("Test email in a DIFFERENT clinic (blank skips live isolation checks): ").strip()
    other_password = getpass.getpass("Other-clinic password (hidden): ") if other_email else ""
    if input("Create and retain DEMO patient/screening/report/audit records? Type YES: ") != "YES":
        return 1
    def check(response, expected: int, label: str):
        if response.status_code != expected:
            # Never print provider bodies, access tokens, passwords or patient data.
            logging.error("FAIL %s: HTTP %s (expected %s)", label, response.status_code, expected)
            raise VerificationFailure(label)
        logging.warning("PASS %s: HTTP %s", label, response.status_code)
        return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.content
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            login = check(client.post("/api/v1/auth/login", json={"email": email, "password": password}), 200, "live login")
            password = ""
            headers = {"Authorization": "Bearer " + login["access_token"]}
            me = check(client.get("/api/v1/auth/me", headers=headers), 200, "same returned token /auth/me")
            allowed_roles = {"technician", "ophthalmologist", "administrator"} if args.ai_report else {"ophthalmologist", "administrator"}
            if me != login["user"] or me["role"] not in allowed_roles:
                logging.error("Profile mismatch or test account is not authorized for the selected workflow.")
                return 1
            check(client.get("/api/v1/patients"), 401, "missing token rejection")
            check(client.get("/api/v1/auth/me", headers={"Authorization": "Bearer intentionally-invalid"}), 401, "invalid token rejection")
            patient = check(client.post("/api/v1/patients", headers=headers, json={
                "mrn": "DEMO-" + uuid.uuid4().hex[:16].upper(), "full_name": "NETRAVA Demo Patient",
                "date_of_birth": "1980-01-01", "gender": "female", "diabetes_type": "type_2",
                "diabetes_duration_years": 10, "latest_hba1c": 7.1, "notes": "Controlled capstone demonstration; synthetic patient.",
            }), 201, "create patient")
            check(client.get("/api/v1/patients", headers=headers), 200, "list patients")
            detail = check(client.get("/api/v1/patients/" + patient["id"], headers=headers), 200, "patient detail")
            if detail["diabetes_duration_years"] != 10:
                raise VerificationFailure("Structured intake roundtrip")
            files = {"image": ("demo-fundus.png" if media == "image/png" else "demo-fundus.jpg", raw, media)}
            screening = check(client.post("/api/v1/screenings", headers=headers, data={"patient_id": patient["id"], "eye": "OD"}, files=files), 201, "screening upload")
            result = check(client.post("/api/v1/predict", params={"retinal_image_id": screening["retinal_image_id"]}, headers=headers, files=files), 200, "real model and persistence")
            if result["persistence_status"] != "persisted" or len(result["probabilities"]) != 5 or not result["explanation"]["heatmap_signed_url"]:
                raise VerificationFailure("Prediction persistence/explanation")
            path = "/api/v1/screenings/" + screening["screening_id"] + "/report"
            saved = None
            if args.ai_report:
                pdf_path = "/api/v1/screenings/" + screening["screening_id"] + "/ai-report/pdf"
                pdf_response = client.get(pdf_path, headers=headers, params={"prediction_id": result["prediction_id"]})
            else:
                review = {"overall_grade": result["predicted_grade"], "grade_override": None, "ophthalmologist_notes": "Controlled synthetic-patient review", "is_urgent_referral": True, "is_signed_off": True}
                saved = check(client.post(path, headers=headers, json=review), 200, "submit report")
                loaded = check(client.get(path, headers=headers), 200, "report roundtrip")
                if saved != loaded or not loaded["is_urgent_referral"]:
                    raise VerificationFailure("Report field roundtrip")
                pdf_path = path + "/pdf"
                pdf_response = client.get(pdf_path, headers=headers)
            pdf = check(pdf_response, 200, "AI PDF download" if args.ai_report else "clinical PDF download")
            if pdf_response.headers.get("content-type") != "application/pdf":
                raise VerificationFailure("PDF content type")
            if not pdf.startswith(b"%PDF-"):
                raise VerificationFailure("PDF format")
            if args.ai_report:
                import pymupdf
                with pymupdf.open(stream=pdf, filetype="pdf") as document:
                    text = " ".join(" ".join(page.get_text() for page in document).split())
                    if "NETRAVA AI Screening Report" not in text or sum(len(page.get_image_info()) for page in document) < 2:
                        raise VerificationFailure("AI PDF title or retinal/Grad-CAM image embedding")
            args.pdf_output.parent.mkdir(parents=True, exist_ok=True)
            args.pdf_output.write_bytes(pdf)
            logging.warning("PASS PDF saved locally. Android viewer opening must be verified separately in the app.")
            # Validate signed media with no bearer/service key attached.
            import httpx
            for url in [screening["fundus_image_signed_url"], result["explanation"]["heatmap_signed_url"]]:
                if not url.startswith("https://"):
                    raise VerificationFailure("Signed media requires HTTPS")
                response = httpx.get(url, timeout=20)
                if response.status_code != 200:
                    raise VerificationFailure("Signed media download")
                from urllib.parse import urlsplit, urlunsplit
                parsed = urlsplit(url)
                public_url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path.replace("/object/sign/", "/object/public/"), "", ""))
                if httpx.get(public_url, timeout=20).status_code == 200:
                    raise VerificationFailure("Medical media is publicly accessible")
            if other_email:
                other = check(client.post("/api/v1/auth/login", json={"email": other_email, "password": other_password}), 200, "other clinic login")
                other_password = ""
                other_headers = {"Authorization": "Bearer " + other["access_token"]}
                check(client.get("/api/v1/patients/" + patient["id"], headers=other_headers), 404, "cross-clinic patient rejection")
                check(client.get(path, headers=other_headers), 404, "cross-clinic report rejection")
                check(client.get(pdf_path, headers=other_headers, params={"prediction_id": result["prediction_id"]} if args.ai_report else None), 404, "cross-clinic PDF rejection")
                check(client.post("/api/v1/predict", params={"retinal_image_id": screening["retinal_image_id"]}, headers=other_headers, files=files), 404, "cross-clinic image rejection")
                rest_headers = {**other_headers, "apikey": settings.SUPABASE_KEY}
                records = [("patients", patient["id"]), ("screenings", screening["screening_id"]), ("retinal_images", screening["retinal_image_id"]), ("predictions", result["prediction_id"])]
                if saved is not None:
                    records.append(("reports", saved["id"]))
                for table, identifier in records:
                    response = httpx.get(settings.SUPABASE_URL.rstrip("/") + "/rest/v1/" + table, headers=rest_headers, params={"select": "id", "id": "eq." + identifier}, timeout=20)
                    if response.status_code != 200 or response.json() != []:
                        raise VerificationFailure("Live RLS isolation failure")
                logging.warning("PASS live cross-clinic API and RLS checks.")
            else:
                logging.warning("NOT VERIFIED: live cross-clinic API/RLS; rerun with a second-clinic account.")
            logging.warning("PASS live screening/report workflow; demo records and immutable audit events retained.")
            if not other_email:
                return 2
        return 0
    except VerificationFailure as exc:
        logging.error("Verification stopped: %s", str(exc))
        return 1
    except Exception as exc:
        logging.error("Verification stopped: %s. No secrets or response bodies were printed.", type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
