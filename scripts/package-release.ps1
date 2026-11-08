<#
.SYNOPSIS
    Prepare les artefacts de distribution a partir de dist\NexusDesk (produit par build.ps1) :
    archive portable ZIP, installateur Inno Setup, VERSION.txt et SHA256SUMS.txt.
.DESCRIPTION
    Les artefacts sont ecrits dans release\<version>\ (ignore par Git). La version d'affichage
    est derivee de pyproject.toml (PEP 440 -> SemVer : 0.2.1b1 -> 0.2.1-beta.1).
    L'installateur n'est produit que si ISCC.exe (Inno Setup 6) est disponible.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

function ConvertTo-DisplayVersion([string]$pep440) {
    $m = [regex]::Match($pep440, '^(\d+\.\d+\.\d+)(?:(a|b|rc)(\d+))?$')
    if (-not $m.Success) { return $pep440 }
    if (-not $m.Groups[2].Success) { return $m.Groups[1].Value }
    $label = @{ "a" = "alpha"; "b" = "beta"; "rc" = "rc" }[$m.Groups[2].Value]
    return "$($m.Groups[1].Value)-$label.$($m.Groups[3].Value)"
}

function Find-Iscc {
    $command = Get-Command iscc -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    foreach ($candidate in @(
            (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
            (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
            (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"))) {
        if ($candidate -and (Test-Path $candidate)) { return $candidate }
    }
    return $null
}

Push-Location $repoRoot
try {
    $pyproject = Get-Content "pyproject.toml" -Raw
    $pep440 = [regex]::Match($pyproject, 'version\s*=\s*"([^"]+)"').Groups[1].Value
    $version = ConvertTo-DisplayVersion $pep440
    $distDir = Join-Path $repoRoot "dist\NexusDesk"
    if (-not (Test-Path (Join-Path $distDir "NexusDesk.exe"))) {
        throw "dist\NexusDesk\NexusDesk.exe introuvable : lancez d'abord scripts/build.ps1."
    }

    $releaseDir = Join-Path $repoRoot "release\$version"
    if (Test-Path $releaseDir) {
        throw "Le dossier $releaseDir existe deja : deplacez-le avant de reconstruire (aucune suppression automatique)."
    }
    New-Item -ItemType Directory -Force $releaseDir | Out-Null
    Write-Host "Version : $version (PEP 440 : $pep440)" -ForegroundColor Cyan

    $commit = (git rev-parse --short HEAD).Trim()
    $versionInfo = @(
        "NexusDesk $version",
        "Version PEP 440 : $pep440",
        "Commit : $commit",
        "Date de construction : $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss zzz'))",
        "Plateforme : Windows 10/11 64 bits (x64)",
        "Python embarque : $((uv run python -c 'import platform; print(platform.python_version())').Trim())",
        "PySide6 : $((uv run python -c 'import PySide6; print(PySide6.__version__)').Trim())"
    )
    $versionInfo | Set-Content -Path (Join-Path $releaseDir "VERSION.txt") -Encoding utf8

    Write-Host "== Archive portable ==" -ForegroundColor Cyan
    $stagingRoot = Join-Path $releaseDir "_staging"
    $portableName = "NexusDesk-$version-win64-portable"
    $portableDir = Join-Path $stagingRoot $portableName
    Copy-Item -Path $distDir -Destination $portableDir -Recurse
    # Mode portable (section 14) : donnees a cote de l'executable, rien dans %LOCALAPPDATA%.
    Set-Content -Path (Join-Path $portableDir "portable.flag") -Value "" -Encoding ascii
    Copy-Item "README.md", "CHANGELOG.md" -Destination $portableDir
    Copy-Item (Join-Path $releaseDir "VERSION.txt") -Destination $portableDir
    $zipPath = Join-Path $releaseDir "$portableName.zip"
    Compress-Archive -Path $portableDir -DestinationPath $zipPath -CompressionLevel Optimal
    Remove-Item -Recurse -Force $stagingRoot   # copie temporaire creee par ce script

    $iscc = Find-Iscc
    if ($iscc) {
        Write-Host "== Installateur Inno Setup ==" -ForegroundColor Cyan
        & $iscc "/Q" "/DAppVersion=$version" "/DSourceDir=$distDir" "/DOutputDir=$releaseDir" "installer\nexusdesk.iss"
        if ($LASTEXITCODE -ne 0) { throw "ISCC a echoue (code $LASTEXITCODE)" }
    }
    else {
        Write-Warning "Inno Setup (ISCC.exe) introuvable : installateur non produit."
    }

    Write-Host "== Empreintes SHA-256 ==" -ForegroundColor Cyan
    $sums = Get-ChildItem -Path $releaseDir -File | Where-Object { $_.Name -ne "SHA256SUMS.txt" } | Sort-Object Name | ForEach-Object {
        "$((Get-FileHash -Path $_.FullName -Algorithm SHA256).Hash.ToLower())  $($_.Name)"
    }
    $sums | Set-Content -Path (Join-Path $releaseDir "SHA256SUMS.txt") -Encoding ascii

    Get-ChildItem -Path $releaseDir -File | ForEach-Object {
        Write-Host ("{0,-50} {1,8:N1} Mo" -f $_.Name, ($_.Length / 1MB))
    }
    Write-Host "Artefacts prets : $releaseDir" -ForegroundColor Green
}
finally {
    Pop-Location
}
