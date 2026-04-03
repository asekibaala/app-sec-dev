# URL Recon

URL Recon is a domain reconnaissance application with a FastAPI backend and a React frontend. It runs scans, stores results, and can export completed scans as HTML or PDF reports.

## Stack

- Backend: FastAPI
- Frontend: React + Vite
- Reports: Jinja2 HTML templates, optional PDF generation through WeasyPrint

## Run Locally

### Backend

Create and activate a Python environment, install dependencies, then start the API from the `backend` directory.

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The API listens on `http://localhost:8000`.

### Frontend

From the `frontend` directory:

```bash
npm install
npm run dev
```

The frontend listens on `http://localhost:5173`.

## Report Exports

HTML report export works with the Python dependencies already in this repo.

PDF export uses WeasyPrint and also requires native system libraries. If these libraries are missing:

- The backend will still start
- HTML export will still work
- PDF export will return `503 Service Unavailable`
- `GET /api/health` will report `"pdf_reports_available": false`

This is intentional graceful degradation. The backend does not crash when PDF dependencies are absent.

## Linux Deployment Requirements

For Linux and Unix-like deployments, treat WeasyPrint's native libraries as system dependencies of the backend, not just Python package dependencies.

WeasyPrint's official installation guide says Linux installs should use the system package manager where possible, and that Pango is a required dependency.

Official docs:

- https://doc.courtbouillon.org/weasyprint/stable/first_steps.html
- https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#troubleshooting

### Debian / Ubuntu / Kali

If you install WeasyPrint in a Python virtual environment, install these OS packages first:

```bash
sudo apt update
sudo apt install -y python3-pip libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0
```

If you need to build without wheels or hit image/ffi build issues, install the extended set:

```bash
sudo apt install -y python3-pip libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 libffi-dev libjpeg-dev libopenjp2-7-dev
```

Then install Python dependencies:

```bash
pip install -r backend/requirements.txt
```

### Fedora

```bash
sudo dnf install -y python-pip pango
pip install -r backend/requirements.txt
```

If building without wheels:

```bash
sudo dnf install -y python3-pip pango gcc python3-devel gcc-c++ zlib-devel libjpeg-devel openjpeg2-devel libffi-devel
```

### Arch

```bash
sudo pacman -S --needed python-pip pango
pip install -r backend/requirements.txt
```

If building without wheels:

```bash
sudo pacman -S --needed python-pip pango gcc libjpeg-turbo openjpeg2
```

## Operational Check

Use the health endpoint to confirm whether PDF export is available in the current runtime:

```bash
curl http://localhost:8000/api/health
```

Expected response when PDF export is available:

```json
{
  "status": "ok",
  "message": "URL Recon API is running",
  "pdf_reports_available": true
}
```

Expected response when native WeasyPrint libraries are missing:

```json
{
  "status": "ok",
  "message": "URL Recon API is running",
  "pdf_reports_available": false,
  "pdf_reports_error": "..."
}
```

## Deployment Guidance

For repeatable cross-distro deployments, a container image is the cleanest option because it lets you install and pin the required native packages explicitly.

If you deploy directly onto target machines, document the distro-specific package prerequisites and install them before starting the backend service.
