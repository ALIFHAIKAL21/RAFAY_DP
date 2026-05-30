param(
    [int]$Port = 8503
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$performanceScript = Join-Path $root "performance.py"
$pythonExe = (Get-Command python -ErrorAction Stop).Source

if (-not (Test-Path -LiteralPath $performanceScript)) {
    throw "File tidak ditemukan: $performanceScript"
}

Start-Process -FilePath $pythonExe -WorkingDirectory $root -ArgumentList @(
    "-m", "streamlit", "run", $performanceScript, "--server.port", "$Port"
) | Out-Null

Write-Host "performance.py running on: http://localhost:$Port"
