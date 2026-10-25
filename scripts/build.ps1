<#
.SYNOPSIS
    Empaquette NexusDesk avec PyInstaller (mode dossier) et calcule les empreintes SHA-256.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

Push-Location $repoRoot
try {
    $pyprojectContent = Get-Content "pyproject.toml" -Raw
    $versionMatch = [regex]::Match($pyprojectContent, 'version\s*=\s*"([^"]+)"')
    $version = if ($versionMatch.Success) { $versionMatch.Groups[1].Value } else { "0.0.0" }
    Write-Host "Version : $version" -ForegroundColor Cyan

    Write-Host "== PyInstaller (mode dossier) ==" -ForegroundColor Cyan
    uv run pyinstaller nexusdesk.spec --noconfirm --clean
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller a echoue (code $LASTEXITCODE)"
    }

    $distDir = Join-Path "dist" "NexusDesk"
    if (-not (Test-Path $distDir)) {
        throw "Le dossier empaquete '$distDir' n'a pas ete produit."
    }

    Write-Host "== Empreintes SHA-256 ==" -ForegroundColor Cyan
    $manifestPath = Join-Path $distDir "SHA256SUMS.txt"
    $lines = @()
    Get-ChildItem -Path $distDir -Recurse -File | Where-Object { $_.Name -ne "SHA256SUMS.txt" } | ForEach-Object {
        $hash = Get-FileHash -Path $_.FullName -Algorithm SHA256
        $relativePath = $_.FullName.Substring($distDir.Length + 1)
        $lines += "$($hash.Hash)  $relativePath"
    }
    $lines | Set-Content -Path $manifestPath -Encoding utf8
    Write-Host "Manifest ecrit dans $manifestPath"

    $exePath = Join-Path $distDir "NexusDesk.exe"
    if (-not (Test-Path $exePath)) {
        throw "L'executable '$exePath' est introuvable apres l'empaquetage."
    }

    $installedSizeMb = [math]::Round(((Get-ChildItem -Path $distDir -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB), 1)
    Write-Host "Taille installee : $installedSizeMb Mo (objectif < 150 Mo)" -ForegroundColor Cyan

    Write-Host "Empaquetage NexusDesk $version termine : $distDir" -ForegroundColor Green
}
finally {
    Pop-Location
}
