[CmdletBinding()]
param(
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'status',
    [ValidateSet('all', 'backend', 'ngrok')]
    [string]$Service = 'all'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $root 'tmp/netrava'
$python = Join-Path $root '.venv/Scripts/python.exe'
$backendPort = 8000
$localOrigin = "http://127.0.0.1:$backendPort"
$healthPath = '/api/v1/health'
$ngrokPackage = 'C:\Program Files\WindowsApps\ngrok.ngrok_3.39.11.0_x64__1g87z0zv29zzc\ngrok.exe'

function Get-Listeners {
    # netstat works in ordinary Windows terminals without administrative privileges.
    $connections = & netstat.exe -ano
    if ($LASTEXITCODE -ne 0) { throw 'Could not enumerate TCP listeners.' }
    foreach ($line in $connections) {
        if ($line -match '^\s*TCP\s+(\S+):(\d+)\s+\S+\s+LISTENING\s+(\d+)\s*$') {
            [pscustomobject]@{ Address = $Matches[1]; Port = [int]$Matches[2]; Id = [int]$Matches[3] }
        }
    }
}

function Get-Health([string]$Origin) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "$Origin$healthPath" `
            -Headers @{ 'ngrok-skip-browser-warning' = '1' } -TimeoutSec 8 `
            -MaximumRedirection 0 -ErrorAction Stop
        $body = $response.Content | ConvertFrom-Json
        if ($response.StatusCode -eq 200 -and $response.Headers['X-Process-Time-Ms'] -and
            $body.status -in @('healthy', 'degraded') -and $body.model_loaded -is [bool] -and
            $body.database_connected -is [bool] -and $body.version -and $body.environment -and $body.timestamp) {
            return $body
        }
    } catch {
        Write-Verbose ("Health request failed for {0}: {1}" -f $Origin, $_.Exception.Message)
    }
}

function Format-Health($Health) {
    if (!$Health) { return 'unreachable or unexpected response' }
    return "$($Health.status) (model loaded: $($Health.model_loaded), database connected: $($Health.database_connected))"
}

function Get-ManagedProcess([string]$Name) {
    $file = Join-Path $runtime "$Name.json"
    if (!(Test-Path -LiteralPath $file)) { return }
    $record = Get-Content -LiteralPath $file -Raw | ConvertFrom-Json
    $process = Get-Process -Id $record.id -ErrorAction SilentlyContinue
    # Compare creation time as well as PID so a recycled PID cannot be stopped.
    if ($process -and $process.StartTime.ToUniversalTime().Ticks.ToString() -eq $record.started) {
        return $process
    }
    Remove-Item -LiteralPath $file
}

function Start-ManagedProcess([string]$Name, [string]$Executable, [string[]]$Arguments) {
    $process = Start-Process -FilePath $Executable -ArgumentList $Arguments -WorkingDirectory $root `
        -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtime "$Name.stdout.log") `
        -RedirectStandardError (Join-Path $runtime "$Name.stderr.log") -PassThru
    try {
        @{ id = $process.Id; started = $process.StartTime.ToUniversalTime().Ticks.ToString() } |
            ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $runtime "$Name.json") -Encoding ascii
    } catch {
        if (!$process.HasExited) {
            & taskkill.exe /PID $process.Id /T /F | Out-Null
        }
        throw
    }
    return $process
}

function Stop-ManagedProcess([string]$Name) {
    $process = Get-ManagedProcess $Name
    if (!$process) {
        Write-Host "$Name has no managed process."
        return
    }
    # The Windows venv Python launcher can host Uvicorn in a child process.
    & taskkill.exe /PID $process.Id /T /F
    if ($LASTEXITCODE -ne 0 -and !$process.HasExited) {
        throw "Could not stop managed $Name (PID $($process.Id))."
    }
    if (!$process.WaitForExit(5000)) { throw "Managed $Name did not exit." }
    Remove-Item -LiteralPath (Join-Path $runtime "$Name.json")
}

function Find-Tunnels {
    $agents = @(Get-Process -Name ngrok -ErrorAction SilentlyContinue)
    if (!$agents.Count) { return }
    $ports = Get-Listeners | Where-Object {
        $_.Id -in $agents.Id -and $_.Address -in @('127.0.0.1', '0.0.0.0')
    }
    foreach ($listener in $ports) {
        try {
            $api = Invoke-RestMethod -Uri "http://127.0.0.1:$($listener.Port)/api/tunnels" `
                -TimeoutSec 2 -MaximumRedirection 0 -ErrorAction Stop
        } catch { continue }
        foreach ($tunnel in $api.tunnels) {
            $public = $null
            if ($tunnel.config.addr -match "^http://(localhost|127\.0\.0\.1|\[::1\]):$backendPort/?$" -and
                [uri]::TryCreate($tunnel.public_url, [UriKind]::Absolute, [ref]$public) -and
                $public.Scheme -eq 'https' -and !$public.UserInfo -and $public.AbsolutePath -eq '/' -and
                !$public.Query -and !$public.Fragment) {
                [pscustomobject]@{
                    Url = $public.GetLeftPart([UriPartial]::Authority)
                    Id = $listener.Id
                    Inspect = $tunnel.config.inspect
                }
            }
        }
    }
}

function Start-Backend {
    if (!(Test-Path -LiteralPath $python -PathType Leaf)) {
        throw 'Missing .venv\Scripts\python.exe. See docs/architecture/windows_development.md.'
    }
    # Import the app to check runtime dependencies and settings without warming the model.
    $ErrorActionPreference = 'Continue'
    & $python -c 'import uvicorn; from backend.app.main import app; from ai_model.inference import predictor' 2>$null
    $importExitCode = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($importExitCode -ne 0) {
        throw 'Backend preflight failed. Check .venv dependencies and backend settings. See docs/architecture/windows_development.md.'
    }
    $listeners = @(Get-Listeners | Where-Object Port -eq $backendPort)
    if ($listeners.Count) {
        $local = Get-Health $localOrigin
        if ($local.status -eq 'healthy') {
            Write-Host "Reusing NETRAVA backend on port $backendPort."
            return
        }
        $owners = foreach ($processId in ($listeners.Id | Sort-Object -Unique)) {
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            "$($process.ProcessName) (PID $processId)"
        }
        throw "Port $backendPort is occupied by $($owners -join ', '). Local health: $(Format-Health $local)."
    }
    if (Get-ManagedProcess 'backend') { throw 'Managed backend exists without a listener. Check logs or run netrava restart.' }

    $oldDocs = $env:NETRAVA_DISABLE_API_DOCS
    try {
        $env:NETRAVA_DISABLE_API_DOCS = 'true'
        $process = Start-ManagedProcess 'backend' $python @(
            '-m', 'uvicorn', 'backend.app.main:app', '--host', '127.0.0.1', '--port', "$backendPort", '--workers', '1'
        )
        $script:startedBackend = $true
    } finally {
        $env:NETRAVA_DISABLE_API_DOCS = $oldDocs
    }
    Write-Host "Waiting for FastAPI (managed PID $($process.Id))..."
    $deadline = (Get-Date).AddSeconds(120)
    do {
        if ($process.HasExited) { break }
        $local = Get-Health $localOrigin
        if ($local.status -eq 'healthy' -and !$process.HasExited) { return }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "Backend did not become healthy. Last check: $(Format-Health $local). See tmp/netrava/backend.stderr.log."
}

function Start-Tunnel {
    $local = Get-Health $localOrigin
    if ($local.status -ne 'healthy') { throw "Local NETRAVA health: $(Format-Health $local)." }
    $tunnel = Find-Tunnels | Select-Object -First 1
    if ($tunnel) {
        Write-Host "Reusing ngrok tunnel (PID $($tunnel.Id))."
    } else {
        if (Get-ManagedProcess 'ngrok') { throw 'Managed ngrok exists without a matching tunnel. Check logs or run netrava restart.' }
        $executable = $ngrokPackage
        if (!(Test-Path -LiteralPath $executable -PathType Leaf)) {
            $executable = (Get-Command ngrok.exe -CommandType Application -ErrorAction SilentlyContinue).Source
            if (!$executable) {
                $alias = Join-Path $env:LOCALAPPDATA 'Microsoft/WindowsApps/ngrok.exe'
                if (Test-Path -LiteralPath $alias -PathType Leaf) { $executable = $alias }
            }
        }
        if (!$executable) { throw 'ngrok.exe was not found in the configured package path, PATH, or Windows app aliases.' }
        # With no explicit URL, ngrok uses the account's assigned development domain.
        $process = Start-ManagedProcess 'ngrok' $executable @(
            'http', $localOrigin, '--inspect=false', '--log=stdout'
        )
        $script:startedNgrok = $true
        Write-Host "Waiting for ngrok (managed PID $($process.Id))..."
        $deadline = (Get-Date).AddSeconds(45)
        do {
            if ($process.HasExited) { break }
            $tunnel = Find-Tunnels | Where-Object Id -eq $process.Id | Select-Object -First 1
            if ($tunnel) { break }
            Start-Sleep -Seconds 1
        } while ((Get-Date) -lt $deadline)
        if (!$tunnel) { throw 'ngrok did not publish an HTTPS tunnel. See tmp/netrava/ngrok.stdout.log and ngrok.stderr.log.' }
    }

    Write-Host "Public forwarding URL: $($tunnel.Url)"
    Write-Host "Android API base URL: $($tunnel.Url)/api/v1"
    if ($tunnel.Inspect -ne $false) { Write-Host 'Existing tunnel has request inspection enabled or its setting is unknown.' }
    for ($attempt = 0; $attempt -lt 3; $attempt++) {
        $public = Get-Health $tunnel.Url
        if ($public.status -eq 'healthy') {
            Write-Host "Public health: $(Format-Health $public)"
            return
        }
        if ($attempt -lt 2) { Start-Sleep -Seconds 2 }
    }
    throw "Public health: $(Format-Health $public)."
}

function Show-Status {
    $listeners = @(Get-Listeners | Where-Object Port -eq $backendPort)
    $local = Get-Health $localOrigin
    $backend = Get-ManagedProcess 'backend'
    if ($local) { Write-Host "Backend: $($local.status)" }
    elseif ($listeners.Count) { Write-Host 'Backend: port occupied or health unavailable' }
    else { Write-Host 'Backend: no listener' }
    $listenerIds = ($listeners.Id | Sort-Object -Unique) -join ', '
    if (!$listenerIds) { $listenerIds = 'none' }
    Write-Host "Backend PID (port listener): $listenerIds"
    if ($backend) { Write-Host "Managed backend PID: $($backend.Id)" }
    Write-Host "Local health: $(Format-Health $local)"

    $tunnels = @(Find-Tunnels)
    if (!$tunnels.Count) {
        Write-Host 'ngrok: no matching HTTPS tunnel'
        Write-Host 'Public forwarding URL: unavailable'
        Write-Host 'Public health: unavailable'
        return
    }
    $agent = Get-ManagedProcess 'ngrok'
    foreach ($tunnel in $tunnels) {
        $ownership = if ($agent -and $tunnel.Id -eq $agent.Id) { 'managed' } else { 'external' }
        Write-Host "ngrok: forwarding ($ownership, PID $($tunnel.Id), inspection: $($tunnel.Inspect))"
        Write-Host "Public forwarding URL: $($tunnel.Url)"
        Write-Host "Public health: $(Format-Health (Get-Health $tunnel.Url))"
    }
}

$lock = $null
$startedBackend = $false
$startedNgrok = $false
try {
    Set-Location -LiteralPath $root
    New-Item -ItemType Directory -Path $runtime -Force | Out-Null
    try {
        $lock = [IO.File]::Open((Join-Path $runtime 'manager.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
    } catch [IO.IOException] {
        throw 'Another NETRAVA command is in progress. Try again when it finishes.'
    }
    if ($Action -eq 'status') {
        Show-Status
        exit 0
    }
    if ($Action -in @('stop', 'restart')) {
        if ($Service -in @('all', 'ngrok')) { Stop-ManagedProcess 'ngrok' }
        if ($Service -in @('all', 'backend')) { Stop-ManagedProcess 'backend' }
    }
    if ($Action -in @('start', 'restart')) {
        if ($Service -in @('all', 'backend')) { Start-Backend }
        if ($Service -in @('all', 'ngrok')) { Start-Tunnel }
    }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
    foreach ($name in @('ngrok', 'backend')) {
        if (($name -eq 'ngrok' -and $startedNgrok) -or ($name -eq 'backend' -and $startedBackend)) {
            try { Stop-ManagedProcess $name }
            catch { Write-Host "Cleanup error: $($_.Exception.Message)" }
        }
    }
    exit 1
} finally {
    if ($lock) { $lock.Dispose() }
}
