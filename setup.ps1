# One-time setup: virtual environment, dependencies, Playwright browser, .env file.
# Run from the project root:  .\setup.ps1
$ErrorActionPreference = "Stop"

if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Created .env - open it and fill in BASE_URL, APP_USER and APP_PASSWORD."
}

Write-Host "Running the framework self-check (needs no application)..."
.\.venv\Scripts\python.exe -m pytest -m selfcheck
