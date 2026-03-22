param(
    [switch]$UseApplicationDefault
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    throw "Required command not found: gcloud"
}

if ($UseApplicationDefault) {
    gcloud auth application-default print-access-token
    exit $LASTEXITCODE
}

gcloud auth print-access-token
