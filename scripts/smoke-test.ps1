<#
.SYNOPSIS
    Demarre l'executable empaquete, verifie ressources/chemins/base, puis le ferme proprement.
    N'utilise pas Python : seulement des appels .NET, pour rester valide dans un environnement
    sans Python (Windows Sandbox, section 18).
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$exePath = Join-Path $repoRoot "dist\NexusDesk\NexusDesk.exe"

if (-not (Test-Path $exePath)) {
    throw "Executable introuvable : $exePath. Lancez d'abord scripts/build.ps1."
}

function Send-NexusDeskCommand {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [int]$TimeoutMs = 3000
    )
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "NexusDesk", [System.IO.Pipes.PipeDirection]::InOut)
    try {
        $pipe.Connect($TimeoutMs)
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Command)
        $pipe.Write($bytes, 0, $bytes.Length)
        $pipe.Flush()
        $buffer = New-Object byte[] 4096
        $read = $pipe.Read($buffer, 0, $buffer.Length)
        return [System.Text.Encoding]::UTF8.GetString($buffer, 0, $read)
    }
    finally {
        $pipe.Dispose()
    }
}

$dataDir = Join-Path $env:LOCALAPPDATA "NexusDesk"
$env:NEXUSDESK_ALLOW_IPC_QUIT = "1"

Write-Host "== Demarrage de NexusDesk.exe ==" -ForegroundColor Cyan
$process = Start-Process -FilePath $exePath -PassThru

try {
    Write-Host "== Attente de l'initialisation (dossiers de donnees) ==" -ForegroundColor Cyan
    $deadline = (Get-Date).AddSeconds(15)
    while (-not (Test-Path (Join-Path $dataDir "logs\nexusdesk.log")) -and (Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 300
    }
    if (-not (Test-Path (Join-Path $dataDir "logs\nexusdesk.log"))) {
        throw "Le journal n'a pas ete cree dans le delai attendu : NexusDesk n'a pas demarre correctement."
    }
    foreach ($subdir in @("data", "backups", "logs")) {
        if (-not (Test-Path (Join-Path $dataDir $subdir))) {
            throw "Dossier de donnees manquant : $subdir"
        }
    }
    Write-Host "Dossiers de donnees presents (data, backups, logs)." -ForegroundColor Green

    if ($process.HasExited) {
        throw "Le processus NexusDesk s'est termine de maniere inattendue (code $($process.ExitCode))."
    }

    Write-Host "== Test de reouverture via le tube nomme (OPEN_MAIN_WINDOW) ==" -ForegroundColor Cyan
    $response = Send-NexusDeskCommand -Command "OPEN_MAIN_WINDOW"
    if ($response -ne "ACK") {
        throw "Reponse inattendue du tube nomme : '$response'"
    }
    Write-Host "Commande OPEN_MAIN_WINDOW acquittee." -ForegroundColor Green

    Write-Host "== Arret propre via le tube nomme (QUIT) ==" -ForegroundColor Cyan
    Send-NexusDeskCommand -Command "QUIT" | Out-Null

    $deadline = (Get-Date).AddSeconds(10)
    while (-not $process.HasExited -and (Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 200
    }
    if (-not $process.HasExited) {
        throw "NexusDesk ne s'est pas arrete proprement dans le delai attendu apres QUIT."
    }
    Write-Host "Arret propre confirme (code de sortie $($process.ExitCode))." -ForegroundColor Green

    Write-Host "Test de fumee reussi." -ForegroundColor Green
}
finally {
    if (-not $process.HasExited) {
        Write-Warning "Arret forcé du processus NexusDesk (le test de fumee a echoue avant l'arret propre)."
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }
}
