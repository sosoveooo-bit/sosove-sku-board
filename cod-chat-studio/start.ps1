param([switch]$Restart)
$ErrorActionPreference = 'Stop'
$studioRoot = $PSScriptRoot
$pythonPath = Join-Path (Split-Path $studioRoot -Parent) '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) { throw 'Project virtualenv is missing: .venv\Scripts\python.exe' }
& $pythonPath (Join-Path $studioRoot 'server.py') --check-compiler
if ($LASTEXITCODE -ne 0) { throw 'Compiler dependency check failed; the existing service has not been stopped.' }
$listener = Get-NetTCPConnection -LocalPort 8795 -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    $health = $null
    try { $health = Invoke-RestMethod 'http://127.0.0.1:8795/health' -TimeoutSec 3 }
    catch { if (-not $Restart) { throw 'Studio health check failed. Run start.ps1 -Restart after active tasks finish.' } }
    if ($health -and $health.service -ne 'cod-chat-studio') { throw 'Port 8795 is occupied by another application' }
    if (-not $Restart) {
        if (-not $health.compilerReady -or -not $health.projectVenv) { throw 'Existing studio uses an old runtime. Run start.ps1 -Restart after active tasks finish.' }
        Write-Output 'http://127.0.0.1:8795/'
        exit
    }
    foreach ($studioPid in @($listener.OwningProcess | Select-Object -Unique)) {
        $process = Get-CimInstance Win32_Process -Filter "ProcessId = $studioPid"
        if ($process.CommandLine -notlike '*cod-chat-studio*server.py*') { throw 'Unexpected process owns port 8795; leaving it unchanged.' }
        Stop-Process -Id $studioPid -ErrorAction Stop
    }
}
Start-Process -FilePath $pythonPath -ArgumentList @('"' + (Join-Path $studioRoot 'server.py') + '"') -WorkingDirectory $studioRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $studioRoot 'stdout.log') -RedirectStandardError (Join-Path $studioRoot 'stderr.log')
Write-Output 'Started COD Chat Studio: http://127.0.0.1:8795/'
