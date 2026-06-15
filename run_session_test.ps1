param(
    [int]$Port = 8502,
    [string]$Address = "127.0.0.1"
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $root "venv\Scripts\python.exe"
$launcher = Join-Path $root "scripts\run_session_test.py"

if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw "Python virtual environment tidak ditemukan: $pythonExe"
}

if (-not (Test-Path -LiteralPath $launcher)) {
    throw "Launcher session test tidak ditemukan: $launcher"
}

& $pythonExe $launcher --port $Port --address $Address
exit $LASTEXITCODE

