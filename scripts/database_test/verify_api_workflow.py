"""Run FastAPI + real inference + actual PostgreSQL RPCs locally.

GoTrue identities and object storage are controlled adapters; SQL and ML are real.
No live account, database or Storage service is contacted.
"""
from __future__ import annotations
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ["ENVIRONMENT"] = "testing"
os.environ["SUPABASE_URL"] = "https://local.invalid"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "controlled-test-key"
from fastapi.testclient import TestClient
import supabase
from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.security import AuthenticatedUser, get_current_user
from backend.app.ml.model_bridge import initialise_predictor


def main() -> None:
    """Exercise API orchestration against the migration's actual SQL functions."""
    settings.ENVIRONMENT = "development"
    process = subprocess.Popen(["node", "scripts/database_test/verify.mjs", "--stdio"], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    try:
        baseline = json.loads(process.stdout.readline())
        assert baseline["failed"] == 0
        def query(sql, params=None):
            process.stdin.write(json.dumps({"sql": sql, "params": params or []}) + "\n")
            process.stdin.flush()
            result = json.loads(process.stdout.readline())
            if "error" in result:
                error = RuntimeError("Controlled SQL test failed")
                error.code = result["error"]["code"]
                raise error
            return result["rows"]
        query("set role service_role")

        class Query:
            def __init__(self, table):
                self.table = table
                self.fields = "*"
                self.filters = []
                self.count = False
                self.sort = ""
                self.bounds = ""
            def select(self, fields, count=None):
                self.fields, self.count = fields, bool(count)
                return self
            def eq(self, field, value):
                self.filters.append((field, value))
                return self
            def limit(self, value):
                self.bounds = f" limit {int(value)}"
                return self
            def range(self, start, end):
                self.bounds = f" limit {int(end-start+1)} offset {int(start)}"
                return self
            def order(self, field, desc=False):
                self.sort = f" order by {field} {'desc' if desc else 'asc'}"
                return self
            def execute(self):
                table, fields = self.table, self.fields
                if "screenings!inner" in fields:
                    table = "retinal_images join screenings on screenings.id=retinal_images.screening_id"
                    fields = "retinal_images.id,retinal_images.content_sha256"
                where = " and ".join(f"{field}=${n}" for n, (field, _) in enumerate(self.filters, 1))
                if "join" in table:
                    where = where.replace("id=", "retinal_images.id=", 1)
                base = f" from {table}" + (" where " + where if where else "")
                params = [v for _, v in self.filters]
                count = int(query("select count(*) as n" + base, params)[0]["n"]) if self.count else None
                return SimpleNamespace(data=query("select " + fields + base + self.sort + self.bounds, params), count=count)

        stored_objects: dict[tuple[str, str], bytes] = {}
        class Bucket:
            def __init__(self, name): self.name = name
            def upload(self, path, contents, options):
                stored_objects[(self.name, path)] = bytes(contents)
            def download(self, path): return stored_objects[(self.name, path)]
            def create_signed_url(self, path, expires_in): return {"signedURL": "https://controlled-storage.invalid/signed"}
            def remove(self, paths):
                for path in paths:
                    stored_objects.pop((self.name, path), None)

        class Client:
            storage = SimpleNamespace(from_=lambda name: Bucket(name))
            def table(self, name): return Query(name)
            def rpc(self, name, payload):
                def execute():
                    args, params = [], []
                    for n, (key, value) in enumerate(payload.items(), 1):
                        cast = "::jsonb" if isinstance(value, dict) else "::smallint" if key in {"p_overall_grade", "p_grade_override"} else ""
                        params.append(json.dumps(value) if isinstance(value, dict) else value)
                        args.append(f"{key} => ${n}{cast}")
                    return SimpleNamespace(data=query(f"select {name}({','.join(args)}) as data", params)[0]["data"])
                return SimpleNamespace(execute=execute)
        original_client = supabase.create_client
        supabase.create_client = lambda *_args: Client()
        def identity(number, role, clinic=1):
            app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(id=f"00000000-0000-0000-0000-{number:012}", role=role, clinic_id=f"00000000-0000-0000-0000-{clinic:012}")
        initialise_predictor()
        from scripts.verification.retinal_fixture import prepare_verification_image
        raw, media, qc = asyncio.run(prepare_verification_image())
        assert qc.is_gradable
        files = {"image": ("verification-retina.png", raw, media)}
        checks = 0
        def expect(response, code):
            nonlocal checks
            assert response.status_code == code, (response.status_code, response.text)
            checks += 1
            return response.json() if "json" in response.headers.get("content-type", "") else response.content
        with TestClient(app, raise_server_exceptions=False) as client:
            identity(10, "technician")
            payload = {"mrn": "API-DEMO-001", "full_name": "Synthetic API Patient", "date_of_birth": "1980-01-01", "gender": "female", "diabetes_type": "type_2", "latest_hba1c": 7.2}
            patient = expect(client.post("/api/v1/patients", json=payload), 201)
            expect(client.post("/api/v1/patients", json=payload), 409)
            expect(client.get("/api/v1/patients"), 200)
            detail = expect(client.get("/api/v1/patients/" + patient["id"]), 200)
            assert detail["latest_hba1c"] == 7.2
            screening = expect(client.post("/api/v1/screenings", data={"patient_id": patient["id"], "eye": "OD"}, files=files), 201)
            prediction = expect(client.post("/api/v1/predict", params={"retinal_image_id": screening["retinal_image_id"]}, files=files), 200)
            assert prediction["persistence_status"] == "persisted"
            assert len(query("select * from prediction_probabilities where prediction_id=$1", [prediction["prediction_id"]])) == 5
            assert prediction["explanation"]["heatmap_base64"]
            ai_path = "/api/v1/screenings/" + screening["screening_id"] + "/ai-report/pdf"
            ai_response = client.get(
                ai_path,
                params={"prediction_id": prediction["prediction_id"]},
            )
            ai_pdf = expect(ai_response, 200)
            assert ai_response.headers["content-type"] == "application/pdf"
            assert ai_response.headers["cache-control"] == "no-store"
            assert ai_pdf.startswith(b"%PDF-")
            import pymupdf
            with pymupdf.open(stream=ai_pdf, filetype="pdf") as document:
                text = " ".join(" ".join(page.get_text() for page in document).split())
                assert "NETRAVA AI Screening Report" in text
                assert "Synthetic API Patient" in text
                assert sum(len(page.get_image_info()) for page in document) >= 2
                assert "Visualization: unavailable" not in text
                assert "Original image unavailable" not in text
            assert query("select id from reports where screening_id=$1", [screening["screening_id"]]) == []
            path = "/api/v1/screenings/" + screening["screening_id"] + "/report"
            expect(client.post(path, json={"overall_grade": 2}), 403)
            identity(11, "ophthalmologist")
            review = {"overall_grade": 2, "grade_override": 3, "ophthalmologist_notes": "Controlled review", "is_urgent_referral": True, "is_signed_off": True}
            saved = expect(client.post(path, json=review), 200)
            loaded = expect(client.get(path), 200)
            assert saved == loaded and loaded["grade_override"] == 3 and loaded["is_urgent_referral"]
            pdf = expect(client.get(path + "/pdf"), 200)
            assert pdf.startswith(b"%PDF-")
            expect(client.post(path, json={**review, "overall_grade": 4}), 409)
            identity(20, "technician", 2)
            expect(client.get(ai_path, params={"prediction_id": prediction["prediction_id"]}), 404)
            expect(client.get("/api/v1/patients/" + patient["id"]), 404)
            expect(client.get(path), 404)
            expect(client.get(path + "/pdf"), 404)
            expect(client.post("/api/v1/screenings", data={"patient_id": patient["id"], "eye": "OD"}, files=files), 404)
            expect(client.post("/api/v1/predict", params={"retinal_image_id": screening["retinal_image_id"]}, files=files), 404)
        print(json.dumps({"api_checks": checks, "sql_checks": baseline["checks"], "actual_model": True, "actual_sql": True, "live_auth": False, "live_storage": False}))
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        if "original_client" in locals(): supabase.create_client = original_client
        process.stdin.close()
        process.wait(timeout=20)


if __name__ == "__main__":
    main()
