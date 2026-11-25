# Windows and Android development

From the repository root in **Command Prompt** (including the CMD profile in VS Code):

```cmd
netrava start
netrava status
netrava restart
netrava stop
```

In **PowerShell**, use `.\netrava.bat start`, and the same prefix for the other commands. Use that form in CMD as well if your terminal disables current-directory command lookup. No PATH or machine execution-policy changes are needed. The batch entry point applies execution policy to its own PowerShell invocation.

The launcher checks imports using `.venv\Scripts\python.exe`, inspects the Windows TCP listeners, and starts a single loopback Uvicorn instance when port 8000 is free. Put the existing backend settings in the root `.env`. To provision a missing environment, run from the root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

The launcher requires `healthy` from NETRAVA, including model readiness and a successful Supabase probe. An occupied port with unexpected or degraded health produces the listener PID and process name. The launcher leaves that process running.

The launcher discovers HTTPS tunnels using the local APIs of running ngrok agents. It reuses one forwarding to local port 8000. When starting its own agent, it uses the installed package, PATH, or the Windows app alias, and ngrok's saved credentials. Keep the agent's local web API enabled and on loopback for discovery. ngrok assigns its stable development domain when the command omits a public hostname. The launcher prints the API base URL it actually discovers, then verifies public health over HTTPS. Failed startup exits with a nonzero code and cleans up processes it launched during that invocation.

The manager stores process IDs, creation times, and separate service logs under `tmp/netrava/`. Stop uses those records and leaves pre-existing processes running. Restart applies the same ownership check before re-running start. The scripts folder also offers `start_backend.bat`, `start_ngrok.bat`, `stop_backend.bat`, `stop_ngrok.bat`, and `status.bat`.

## Android

The Android debug/profile default is `https://bouncing-unquote-lavender.ngrok-free.dev/api/v1`. From the repository root in PowerShell, start NETRAVA, then run:

```powershell
.\netrava.bat start
Set-Location frontend\flutter_app
flutter devices
flutter run -d <ANDROID_DEVICE_ID> --dart-define=API_BASE_URL=https://bouncing-unquote-lavender.ngrok-free.dev/api/v1
```

Replace `<ANDROID_DEVICE_ID>` with the ID from `flutter devices`. The explicit define is optional for debug/profile with the domain above. For an Android emulator using the Windows backend directly, use `--dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1` in a debug build. The define is compiled into the application. Changing it requires a fresh Flutter run or APK build. A tunnel restart on the same domain needs no rebuild. Release builds still require an explicit HTTPS deployment URL.

On the phone, sign in with a dedicated test account and synthetic data. Upload a test image using the screening flow, verify the prediction and Grad-CAM display, then generate and open the AI screening PDF.

## Development data and endpoint exposure

Managed startup disables FastAPI's Swagger, ReDoc and OpenAPI routes and turns off ngrok request inspection. Reused services retain their original settings. If a reused tunnel has inspection enabled or a reused backend exposes API documentation, stop those services from their original terminal and run `netrava start` to use the managed configuration. Public health reports model and database readiness. Application authentication and CORS still follow the backend configuration. Use synthetic data only and keep backend and ngrok credentials in their existing private configuration.
