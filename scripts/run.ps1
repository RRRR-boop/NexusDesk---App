<#
.SYNOPSIS
    Lance NexusDesk depuis les sources.
.PARAMETER Dev
    Active le mode developpeur (journalisation console, etc.).
#>

[CmdletBinding()]
param(
    [switch]$Dev
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

Push-Location $repoRoot
try {
    if ($Dev) {
        uv run python -m nexusdesk -Dev
    }
    else {
        uv run python -m nexusdesk
    }
}
finally {
    Pop-Location
}
