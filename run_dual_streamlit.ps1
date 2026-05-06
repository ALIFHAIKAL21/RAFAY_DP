param(
    [int]$AppPort = 8501,
    [int]$AuditPort = 8502
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$appScript = Join-Path $root "app.py"
$auditScript = Join-Path $root "audit_dashboard.py"
$pythonExe = (Get-Command python -ErrorAction Stop).Source

if (-not (Test-Path -LiteralPath $appScript)) {
    throw "File tidak ditemukan: $appScript"
}

if (-not (Test-Path -LiteralPath $auditScript)) {
    throw "File tidak ditemukan: $auditScript"
}

Start-Process -FilePath $pythonExe -WorkingDirectory $root -ArgumentList @(
    "-m", "streamlit", "run", $appScript, "--server.port", "$AppPort"
) | Out-Null

Start-Process -FilePath $pythonExe -WorkingDirectory $root -ArgumentList @(
    "-m", "streamlit", "run", $auditScript, "--server.port", "$AuditPort"
) | Out-Null

Write-Host "app.py running on: http://localhost:$AppPort"
Write-Host "audit_dashboard.py running on: http://localhost:$AuditPort"
