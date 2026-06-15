$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$env:RAFAY_REVISION_MATCHER_MODEL_PATH = Join-Path $root "models\indobert_spc\final_model"

Write-Host "Using revision matcher model:" $env:RAFAY_REVISION_MATCHER_MODEL_PATH
.\venv\Scripts\python.exe -m streamlit run app.py
