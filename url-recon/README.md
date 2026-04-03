# URL Recon

URL Recon is a two-part application for domain reconnaissance:

- A FastAPI backend that runs WHOIS, DNS, SSL/TLS, HTTP header, and subdomain discovery scans
- A React + Vite frontend that starts scans, polls for results, shows history, and downloads reports

The backend stores every scan on disk under `backend/scans/<scan-id>/`.

## What The App Does

For each target domain, the backend runs these modules in parallel:

- WHOIS lookup
- DNS record enumeration
- SSL/TLS certificate analysis
- HTTP security header analysis
- Subdomain discovery

Completed scans can be exported as:

- HTML reports
- PDF reports through WeasyPrint, if native system libraries are installed

## Requirements

### Core

- Python 3.12 recommended
- Node.js 20+ recommended
- npm

### Python Dependencies

The backend dependencies are pinned in [backend/requirements.txt](/Users/asekibaala/Documents/app-sec-dev/url-recon/backend/requirements.txt).

### Native / OS Dependencies

Some Python packages depend on system libraries or external tools:

- WeasyPrint for PDF export requires native system libraries
- `gobuster` is optional, but improves subdomain discovery on Kali/Parrot systems
- SecLists wordlists are optional, but required if you want Gobuster-based subdomain enumeration

### Network Requirements

The app is not offline-capable. To function fully, the backend host needs outbound network access to:

- Target domains being scanned
- Public DNS resolvers
- WHOIS infrastructure
- `https://crt.sh` for certificate-transparency subdomain discovery

If outbound access is restricted, the app still starts, but individual modules may return partial or empty results.

## Linux Installation

These instructions are the right baseline for Linux distributions such as Kali, Debian, Ubuntu, Fedora, and Arch.

### Debian / Ubuntu / Kali

Install system packages first:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv build-essential libssl-dev libffi-dev
```

If you want PDF export support, also install WeasyPrint's required native libraries:

```bash
sudo apt install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 libjpeg-dev libopenjp2-7-dev
```

If you want Gobuster-based subdomain discovery on Kali/Parrot:

```bash
sudo apt install -y gobuster seclists
```

### Fedora

```bash
sudo dnf install -y python3 python3-pip python3-devel gcc gcc-c++ openssl-devel libffi-devel
```

For PDF export:

```bash
sudo dnf install -y pango
```

For Gobuster:

```bash
sudo dnf install -y gobuster
```

### Arch

```bash
sudo pacman -S --needed python python-pip base-devel openssl libffi
```

For PDF export:

```bash
sudo pacman -S --needed pango
```

For Gobuster:

```bash
sudo pacman -S --needed gobuster
```

## Optional Capabilities

### PDF Export

PDF export is optional. If WeasyPrint's native libraries are missing:

- The backend still starts
- The frontend still works
- HTML report export still works
- PDF export returns HTTP `503`
- `GET /api/health` reports `"pdf_reports_available": false`

This behavior is intentional and already implemented in the backend.

### Gobuster + SecLists

The app always runs:

- Built-in DNS wordlist bruteforce
- crt.sh lookup

It additionally runs Gobuster if available on the host. The code looks for these common Linux wordlists:

- `/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt`
- `/usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt`
- `/usr/share/wordlists/dirb/common.txt`

If Gobuster or these wordlists are missing, the app degrades gracefully and still scans using the built-in methods.

## Backend Setup

From the repo root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn main:app --reload
```

The backend listens on:

- `http://localhost:8000`

Health check:

```bash
curl http://localhost:8000/api/health
```

Expected fields include:

- `status`
- `message`
- `pdf_reports_available`
- `pdf_reports_error` when PDF support is unavailable

## Frontend Setup

From the repo root:

```bash
cd frontend
npm install
npm run dev
```

The frontend listens on:

- `http://localhost:5173`

## Development Wiring

The current development setup assumes:

- Frontend on `http://localhost:5173`
- Backend on `http://localhost:8000`

This is hardcoded in two places:

- CORS allowlist in [backend/main.py](/Users/asekibaala/Documents/app-sec-dev/url-recon/backend/main.py)
- Frontend API base URL in [frontend/src/api/client.js](/Users/asekibaala/Documents/app-sec-dev/url-recon/frontend/src/api/client.js)

If you change ports, hostnames, or deploy behind a real domain, update those files.

## Running The Full App

Start the backend first:

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload
```

In another terminal, start the frontend:

```bash
cd frontend
npm run dev
```

Then open:

```text
http://localhost:5173
```

## Input Validation And Safety Rules

Before any scan is scheduled, the backend validates and normalizes the submitted target in [backend/app/models/validators.py](/Users/asekibaala/Documents/app-sec-dev/url-recon/backend/app/models/validators.py).

Accepted examples:

- `example.com`
- `sub.example.com`
- `https://example.com/path`

The validator strips scheme, path, query, fragment, and port before validating.

The backend rejects:

- Empty targets
- Raw IP addresses
- Private or loopback IP addresses
- `localhost` and similar private hostnames
- `.local` hostnames
- Invalid domain labels
- Hostnames without a TLD

## Reports

Available report endpoints for completed scans:

- `GET /api/scan/{scan_id}/report/html`
- `GET /api/scan/{scan_id}/report/pdf`

Behavior:

- HTML report generation always works if the backend is running normally
- PDF generation requires WeasyPrint native libraries

Generated reports are written into the scan's storage directory:

- `backend/scans/<scan-id>/report.html`
- `backend/scans/<scan-id>/report.pdf`

## Persistence

The application stores scan data on local disk. No external database is required.

Storage location:

- `backend/scans/`

Each scan directory contains:

- `result.json`
- `report.html` when generated
- `report.pdf` when generated successfully

If you delete `backend/scans/`, you delete scan history and generated reports.

## Verification

Backend syntax checks:

```bash
python -m py_compile backend/main.py backend/app/api/routes.py backend/app/models/validators.py backend/app/reports/generator.py
```

Backend validator tests:

```bash
python -m unittest backend.tests.test_validators
```

Frontend production build:

```bash
cd frontend
npm run build
```

## Common Failure Modes

### PDF export unavailable

Symptom:

```json
{"detail":"PDF generation is unavailable because WeasyPrint system libraries are missing."}
```

Meaning:

- WeasyPrint is installed in Python
- Required native libraries such as Pango are not available on the host

Fix on Linux:

- Install the distro-native WeasyPrint dependencies listed above
- Restart the backend
- Recheck `GET /api/health`

### Frontend cannot reach backend

Common causes:

- Backend is not running on port `8000`
- Frontend is not running on port `5173`
- CORS allowlist does not match your frontend origin
- `frontend/src/api/client.js` still points to the wrong backend URL

### Subdomain results are lighter than expected

Common causes:

- `gobuster` is not installed
- SecLists wordlists are not present at the expected paths
- `crt.sh` is unreachable from the host
- DNS/network egress is restricted

## Production Notes

Current code is development-oriented:

- CORS is locked to `http://localhost:5173`
- Frontend API URL is hardcoded to `http://localhost:8000/api`
- Scan results are stored on local disk

Before shipping this in production, you should at minimum review:

- CORS configuration
- frontend API base URL strategy
- scan storage path and retention
- process manager / service supervision
- reverse proxy / TLS termination

## Project Structure

```text
backend/
  app/
    api/
    models/
    reports/
    services/
    storage/
  main.py
  requirements.txt
  tests/
frontend/
  src/
  package.json
README.md
```
