param(
    [int]$Port = 8502
)

$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1

if (-not $listener) {
    Write-Host "Tidak ada server session test yang listen pada port $Port."
    exit 0
}

$processId = [int]$listener.OwningProcess
$processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $processId"
$commandLine = [string]$processInfo.CommandLine

$isSessionTest = (
    $commandLine -match [regex]::Escape("stage2_pair_visual_test copy.py") -and
    $commandLine -match "--server.port\s+$Port"
)

if (-not $isSessionTest) {
    throw (
        "Port $Port digunakan proses lain (PID $processId). " +
        "Stop dibatalkan agar tidak menghentikan aplikasi yang salah."
    )
}

Stop-Process -Id $processId -Force
Write-Host "Server session test pada port $Port dihentikan (PID $processId)."

