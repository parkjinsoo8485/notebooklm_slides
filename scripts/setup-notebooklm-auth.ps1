param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

Require-Command "gcloud"

Write-Host "Setting active gcloud project to: $ProjectId"
gcloud config set project $ProjectId | Out-Host

Write-Host ""
Write-Host "Opening Google user auth flow..."
gcloud auth login | Out-Host

Write-Host ""
Write-Host "Opening Application Default Credentials auth flow..."
gcloud auth application-default login | Out-Host

Write-Host ""
Write-Host "Active gcloud accounts:"
gcloud auth list | Out-Host

Write-Host ""
Write-Host "Current gcloud project:"
gcloud config get-value project | Out-Host

Write-Host ""
Write-Host "NotebookLM auth setup is complete."
