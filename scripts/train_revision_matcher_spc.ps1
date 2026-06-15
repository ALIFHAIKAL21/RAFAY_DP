$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$env:REVISION_MATCH_TRAIN_DATA_PATH = Join-Path $root "data\chat\processed\SPC\revision_matcher_dataset_with_multi_unit_extension_v1.json"
$env:REVISION_MATCH_OUTPUT_DIR_PATH = Join-Path $root "models\indobert_spc"
$env:REVISION_MATCH_MODEL_CHECKPOINT = "indobenchmark/indobert-base-p2"

Write-Host "Training revision matcher..."
Write-Host "Dataset   :" $env:REVISION_MATCH_TRAIN_DATA_PATH
Write-Host "Output dir:" $env:REVISION_MATCH_OUTPUT_DIR_PATH
Write-Host "Checkpoint:" $env:REVISION_MATCH_MODEL_CHECKPOINT

.\venv\Scripts\python.exe -m src.training.train_revision_matcher
