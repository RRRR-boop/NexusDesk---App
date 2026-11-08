<#
.SYNOPSIS
    Prepare les artefacts de distribution a partir de dist\NexusDesk (produit par build.ps1) :
    archive portable ZIP, installateur Inno Setup, VERSION.txt et SHA256SUMS.txt.
.DESCRIPTION
    Les artefacts sont ecrits dans release\<version>\ (ignore par Git). La version d'affichage
    est derivee de pyproject.toml (PEP 440 -> SemVer : 0.2.1b2 -> 0.2.1-beta.2).
    Chaque distribution contient le texte integral de la GNU GPL v3 (LICENSE) et les avis et
    textes de licence des composants tiers embarques (THIRD-PARTY-LICENSES.txt).
    L'installateur n'est produit que si ISCC.exe (Inno Setup 6) est disponible.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$repoUrl = "https://github.com/RRRR-boop/NexusDesk---App"

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

function Write-ThirdPartyLicenses([string]$destination, [string]$version) {
    # Dependances d'execution uniquement (celles embarquees dans l'executable).
    $requirements = uv export --no-dev --no-hashes --no-emit-project --format requirements-txt
    $packages = $requirements | Where-Object { $_ -match '^[A-Za-z0-9]' } | ForEach-Object { ($_ -split '[=<>; ]')[0] } | Sort-Object -Unique
    if (-not $packages) { throw "Impossible de lister les dependances d'execution (uv export)." }
    $inventory = Join-Path $env:TEMP "nexusdesk-third-party-$PID.txt"
    uv run pip-licenses --packages @packages --with-license-file --no-license-path --with-notice-file --format=plain-vertical --output-file $inventory | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "pip-licenses a echoue (code $LASTEXITCODE)" }
    $pythonLicense = uv run python -c "import os, sys; print(open(os.path.join(sys.base_prefix, 'LICENSE.txt'), encoding='utf-8').read())"

    $header = @(
        "NexusDesk $version - avis de licences",
        "==========================================",
        "",
        "NexusDesk est un logiciel libre distribue sous la GNU General Public License v3.0",
        "(GPL-3.0-only) : voir le fichier LICENSE fourni avec cette distribution.",
        "Code source correspondant a cette version : $repoUrl/tree/v$version",
        "",
        "Cette distribution embarque les composants tiers ci-dessous, chacun sous sa propre",
        "licence, toutes compatibles avec la GPL v3. Qt / PySide6 / shiboken6 sont utilises sous",
        "LGPL v3 : leurs bibliotheques sont livrees comme fichiers separes (dossier _internal) et",
        "peuvent etre remplacees par l'utilisateur. Le chargeur PyInstaller est distribue sous",
        "GPL v2 avec une exception explicite autorisant toute licence pour le programme empaquete.",
        "",
        "------------------------------------------------------------------------------",
        "Interpreteur Python $((uv run python -c 'import platform; print(platform.python_version())').Trim()) (python312.dll et bibliotheque standard)",
        "------------------------------------------------------------------------------"
    )
    $separator = @("", "------------------------------------------------------------------------------", "Composants Python tiers (nom, version, licence, texte de licence, avis)", "------------------------------------------------------------------------------", "")
    ($header + $pythonLicense + $separator + (Get-Content $inventory -Encoding utf8)) | Set-Content -Path $destination -Encoding utf8
    Remove-Item $inventory
}

Push-Location $repoRoot
try {
    $pyproject = Get-Content "pyproject.toml" -Raw
    $pep440 = [regex]::Match($pyproject, 'version\s*=\s*"([^"]+)"').Groups[1].Value
    $version = ConvertTo-DisplayVersion $pep440
    $numericVersion = ([regex]::Match($pep440, '^\d+\.\d+\.\d+').Value) + ".0"
    $distDir = Join-Path $repoRoot "dist\NexusDesk"
    if (-not (Test-Path (Join-Path $distDir "NexusDesk.exe"))) {
        throw "dist\NexusDesk\NexusDesk.exe introuvable : lancez d'abord scripts/build.ps1."
    }
    if (-not (Test-Path "LICENSE")) { throw "Fichier LICENSE (GNU GPL v3) introuvable a la racine du depot." }

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
        "Licence : GNU GPL v3 (GPL-3.0-only)",
        "Code source : $repoUrl/tree/v$version",
        "Commit : $commit",
        "Date de construction : $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss zzz'))",
        "Plateforme : Windows 10/11 64 bits (x64)",
        "Python embarque : $((uv run python -c 'import platform; print(platform.python_version())').Trim())",
        "PySide6 : $((uv run python -c 'import PySide6; print(PySide6.__version__)').Trim())"
    )
    $versionInfo | Set-Content -Path (Join-Path $releaseDir "VERSION.txt") -Encoding utf8

    Write-Host "== Dossier d'application (executable + licences) ==" -ForegroundColor Cyan
    $stagingRoot = Join-Path $releaseDir "_staging"
    $appDir = Join-Path $stagingRoot "NexusDesk-v$version-portable"
    Copy-Item -Path $distDir -Destination $appDir -Recurse
    Copy-Item "LICENSE", "README.md", "CHANGELOG.md" -Destination $appDir
    Copy-Item (Join-Path $releaseDir "VERSION.txt") -Destination $appDir
    Write-ThirdPartyLicenses (Join-Path $appDir "THIRD-PARTY-LICENSES.txt") $version

    $iscc = Find-Iscc
    if ($iscc) {
        Write-Host "== Installateur Inno Setup ==" -ForegroundColor Cyan
        & $iscc "/Q" "/DAppVersion=$version" "/DNumericVersion=$numericVersion" "/DSourceDir=$appDir" `
            "/DLicenseFilePath=$(Join-Path $repoRoot 'LICENSE')" "/DOutputDir=$releaseDir" "installer\nexusdesk.iss"
        if ($LASTEXITCODE -ne 0) { throw "ISCC a echoue (code $LASTEXITCODE)" }
    }
    else {
        Write-Warning "Inno Setup (ISCC.exe) introuvable : installateur non produit."
    }

    Write-Host "== Archive portable ==" -ForegroundColor Cyan
    # Mode portable (section 14) : donnees a cote de l'executable, rien dans %LOCALAPPDATA%.
    # Ajoute apres la compilation de l'installateur, qui ne doit pas l'embarquer.
    Set-Content -Path (Join-Path $appDir "portable.flag") -Value "" -Encoding ascii
    $zipPath = Join-Path $releaseDir "NexusDesk-v$version-portable.zip"
    # ZipFile plutot que Compress-Archive : ce dernier echoue si l'antivirus verrouille un
    # instant un fichier fraichement copie ; quelques nouvelles tentatives suffisent.
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    for ($attempt = 1; $attempt -le 5; $attempt++) {
        try {
            [System.IO.Compression.ZipFile]::CreateFromDirectory(
                $appDir, $zipPath, [System.IO.Compression.CompressionLevel]::Optimal, $true)
            break
        }
        catch [System.IO.IOException] {
            if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
            if ($attempt -eq 5) { throw }
            Write-Warning "Fichier verrouille, nouvelle tentative ($attempt/5) : $($_.Exception.Message)"
            Start-Sleep -Seconds 3
        }
    }
    Remove-Item -Recurse -Force $stagingRoot   # copie temporaire creee par ce script

    Write-Host "== Empreintes SHA-256 ==" -ForegroundColor Cyan
    $sums = Get-ChildItem -Path $releaseDir -File | Where-Object { $_.Name -ne "SHA256SUMS.txt" } | Sort-Object Name | ForEach-Object {
        "$((Get-FileHash -Path $_.FullName -Algorithm SHA256).Hash.ToLower())  $($_.Name)"
    }
    # Fins de ligne LF : verifiable aussi bien par Get-FileHash que par « sha256sum -c ».
    [System.IO.File]::WriteAllText((Join-Path $releaseDir "SHA256SUMS.txt"), (($sums -join "`n") + "`n"))

    Get-ChildItem -Path $releaseDir -File | ForEach-Object {
        Write-Host ("{0,-50} {1,8:N1} Mo" -f $_.Name, ($_.Length / 1MB))
    }
    Write-Host "Artefacts prets : $releaseDir" -ForegroundColor Green
}
finally {
    Pop-Location
}
