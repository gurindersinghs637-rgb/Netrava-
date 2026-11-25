# Private live backend verification

From the project root:

```powershell
.\.venv\Scripts\python.exe scripts/verification/verify_live_backend.py
```

At the retinal-image prompt press Enter to use the corrected bundled fixture.
Enter test account credentials privately at the later prompts. Use an account in a
second clinic to include live isolation checks. The script asks for YES before
creating retained synthetic DEMO records and immutable audit events.

The default is derived in memory from the authentic bundled retinal image
`ai_model/tests/data/001639a390f0.png`: RGB, aspect-preserving LANCZOS thumbnail with
a fixed 400x400 bounding box, resulting in 400x266 pixels, lossless PNG encoding.
There is no sharpening, noise injection, cropping or adjustment based on QC score.
The original image is untouched. This derivative passes the existing production
heuristic at blur score 69.47 with optimal illumination on the tested environment.
Passing that heuristic is a software fixture property, not clinical validation.

The previous default at original 3216x2136 resolution scored 6.26. The current
Laplacian-variance calculation uses upload-resolution pixels, so the score changes
with resolution. Production code, its 50.0 threshold and model preprocessing remain
unchanged. No real upload is automatically resized by this verification fix.

All selected images run through the real upload validator and QC before credentials
are requested or database writes occur. Custom images are checked unchanged; an
ungradable one stops the procedure. Identical preflighted bytes are sent to both
screening and prediction so the stored content hash continues to match.

Optional offline preflight, with no prompts, network or database writes:

```powershell
.\.venv\Scripts\python.exe scripts/verification/verify_live_backend.py --check-fixture
```

To check a custom file unchanged, add `--image C:\path\retina.png`.

Exit 0 from the full live procedure means all checks passed. Exit 2 means the
second-clinic checks were omitted. Exit 1 indicates failure. Only the full procedure,
not `--check-fixture`, can establish live backend readiness.
