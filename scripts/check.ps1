<#
.SYNOPSIS
    Verifie la qualite du code : Ruff, mypy --strict, import-linter, pip-audit, licences.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

Push-Location $repoRoot
try {
    Write-Host "== Ruff (lint) ==" -ForegroundColor Cyan
    uv run ruff check src tests

    Write-Host "== Ruff (format) ==" -ForegroundColor Cyan
    uv run ruff format --check src tests

    Write-Host "== mypy --strict ==" -ForegroundColor Cyan
    uv run mypy src

    Write-Host "== import-linter (regles de couches) ==" -ForegroundColor Cyan
    uv run lint-imports

    Write-Host "== pip-audit (vulnerabilites) ==" -ForegroundColor Cyan
    uv run pip-audit

    Write-Host "== Inventaire des licences ==" -ForegroundColor Cyan
    New-Item -ItemType Directory -Force -Path "docs" | Out-Null
    uv run pip-licenses --format=markdown --output-file docs/licences-tierces.md
    Write-Host "Inventaire ecrit dans docs/licences-tierces.md"

    Write-Host "Toutes les verifications sont passees." -ForegroundColor Green
}
finally {
    Pop-Location
}
