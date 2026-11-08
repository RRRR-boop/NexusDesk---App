<#
.SYNOPSIS
    Verifie la qualite du code : Ruff, mypy --strict, import-linter, pip-audit, licences.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][scriptblock]$Command
    )
    Write-Host "== $Label ==" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Echec : $Label (code $LASTEXITCODE)"
    }
}

Push-Location $repoRoot
try {
    Invoke-Step "Ruff (lint)" { uv run ruff check src tests }
    Invoke-Step "Ruff (format)" { uv run ruff format --check src tests }
    Invoke-Step "mypy --strict" { uv run mypy src }
    Invoke-Step "import-linter (regles de couches)" { uv run lint-imports }
    Invoke-Step "pip-audit (vulnerabilites)" { uv run pip-audit }

    Write-Host "== Inventaire des licences ==" -ForegroundColor Cyan
    New-Item -ItemType Directory -Force -Path "docs" | Out-Null
    # Composants tiers uniquement : la licence de NexusDesk (GPL-3.0-only) est dans LICENSE.
    uv run pip-licenses --format=markdown --ignore-packages nexusdesk --output-file docs/licences-tierces.md
    if ($LASTEXITCODE -ne 0) {
        throw "Echec : inventaire des licences (code $LASTEXITCODE)"
    }
    Write-Host "Inventaire ecrit dans docs/licences-tierces.md"

    Write-Host "Toutes les verifications sont passees." -ForegroundColor Green
}
finally {
    Pop-Location
}
