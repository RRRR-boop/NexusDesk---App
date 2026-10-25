<#
.SYNOPSIS
    Lance les tests NexusDesk.
.PARAMETER Integration
    Ajoute les tests d'integration marques "windows" (registre, tubes nommes, processus reels).
.PARAMETER Coverage
    Ajoute le rapport de couverture (texte + HTML dans htmlcov/).
#>

[CmdletBinding()]
param(
    [switch]$Integration,
    [switch]$Coverage
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

Push-Location $repoRoot
try {
    $paths = @("tests/unit", "tests/ui")
    if ($Integration) {
        $paths += "tests/integration"
    }

    $pytestArgs = @($paths)
    if ($Coverage) {
        $pytestArgs += @("--cov=nexusdesk", "--cov-report=term-missing", "--cov-report=html")
    }

    uv run pytest @pytestArgs
}
finally {
    Pop-Location
}
