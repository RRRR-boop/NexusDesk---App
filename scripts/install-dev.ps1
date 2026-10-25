<#
.SYNOPSIS
    Prepare l'environnement de developpement NexusDesk (uv, Python 3.12, hooks pre-commit).
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "== Verification de l'environnement ==" -ForegroundColor Cyan

$osVersion = [System.Environment]::OSVersion.Version
Write-Host "Windows : $osVersion"
if ($osVersion.Major -lt 10) {
    Write-Warning "NexusDesk cible Windows 10 22H2+ ou Windows 11 ; version non testee."
}

$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
    throw "uv est introuvable. Installez-le depuis https://docs.astral.sh/uv/ puis relancez ce script."
}
Write-Host "uv : $(uv --version)"

Push-Location $repoRoot
try {
    Write-Host "== Python 3.12 (via uv) ==" -ForegroundColor Cyan
    uv python install 3.12
    uv python pin 3.12

    Write-Host "== Synchronisation de l'environnement (uv sync) ==" -ForegroundColor Cyan
    uv sync --all-groups

    Write-Host "== Installation des hooks pre-commit ==" -ForegroundColor Cyan
    uv run pre-commit install

    Write-Host "Environnement de developpement pret." -ForegroundColor Green
}
finally {
    Pop-Location
}
