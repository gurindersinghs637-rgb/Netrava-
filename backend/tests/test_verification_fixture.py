"""The live demo fixture must pass production QC without any production override."""
import io
import hashlib
import pytest
from PIL import Image
from scripts.verification.retinal_fixture import prepare_verification_image, SOURCE
from backend.app.services.screening_service import _assess_qc, _QC_BLUR_THRESHOLD


@pytest.mark.asyncio
async def test_default_retinal_fixture_passes_unchanged_production_threshold():
    """Use a fixed-size authentic retinal derivative and preserve its source file."""
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    raw, mime, qc = await prepare_verification_image()
    with Image.open(io.BytesIO(raw)) as image:
        assert image.size == (400, 266)
        assert _assess_qc(image) == qc
    assert mime == "image/png"
    assert _QC_BLUR_THRESHOLD == 50.0
    assert qc.is_gradable and qc.blur_score >= 50.0
    assert qc.illumination == "optimal"
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == before


@pytest.mark.asyncio
async def test_custom_ungradable_image_is_not_resized_or_bypassed():
    """Explicit original-resolution files still fail the production rule."""
    with pytest.raises(ValueError, match="failed production QC"):
        await prepare_verification_image(SOURCE)


@pytest.mark.asyncio
async def test_custom_gradable_image_bytes_are_preserved(tmp_path):
    """Preflight and both live uploads must use the same encoded bytes."""
    raw, _, _ = await prepare_verification_image()
    path = tmp_path / "retina.png"
    path.write_bytes(raw)
    actual, _, _ = await prepare_verification_image(path)
    assert actual == raw


@pytest.mark.parametrize("custom,expected", [(False, 0), (True, 1)])
def test_preflight_cli_never_prompts_or_contacts_live_services(monkeypatch, custom, expected):
    """The fixture can be checked without credentials, logins or database writes."""
    from scripts.verification import verify_live_backend
    args = ["verify_live_backend.py", "--check-fixture"]
    if custom:
        args += ["--image", str(SOURCE)]
    monkeypatch.setattr("sys.argv", args)
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Preflight must not request credentials or access live services")
    monkeypatch.setattr("builtins.input", forbidden)
    monkeypatch.setattr(verify_live_backend, "TestClient", forbidden)
    assert verify_live_backend.main() == expected
