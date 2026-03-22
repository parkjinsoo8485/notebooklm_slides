# NotebookLM Auth Setup

This workspace includes a minimal PowerShell setup for Google Cloud auth that can be used with NotebookLM Enterprise API style workflows.

## Prerequisites

- `gcloud` installed
- A Google Cloud project with the required NotebookLM-related access
- A browser session available for Google login

## Quick start

Run the setup script with your Google Cloud project ID:

```powershell
.\scripts\setup-notebooklm-auth.ps1 -ProjectId "YOUR_GCP_PROJECT_ID"
```

That script will:

- set the active `gcloud` project
- open Google user login with `gcloud auth login`
- create Application Default Credentials with `gcloud auth application-default login`
- print the active account and project

## Get an access token

After setup, get a fresh bearer token with:

```powershell
.\scripts\get-notebooklm-token.ps1
```

If you specifically need an ADC token instead of the standard CLI token:

```powershell
.\scripts\get-notebooklm-token.ps1 -UseApplicationDefault
```

## Current local status

At the time of setup, `gcloud` was installed and the active auth entry was a service account:

- `firebase-adminsdk-fbsvc@afterschool-74294.iam.gserviceaccount.com`

If you need browser-based NotebookLM access under your own Google user, run the setup script so `gcloud auth login` adds your personal account.
