# URL Recon

URL Recon is a two-part reconnaissance application:

- A FastAPI backend that authenticates users, launches domain scans, stores results in PostgreSQL, and serves downloadable reports
- A React + Vite frontend that provides a login page, a scan workspace, and a sidebar for browsing previous scans

## Current Features

- Login page backed by PostgreSQL users
- Default seeded admin account
- Passwords stored as salted PBKDF2 hashes, never in plaintext
- Signed bearer-token authentication for protected API routes
- Per-domain scan cooldown: `60` seconds
- Per-IP scan rate limit: `10` requests per `60` seconds
- Scan history sidebar for reopening previous scans
- HTML and PDF report downloads for completed scans

## Default Login

On first backend startup, the app creates a default admin account if it does not already exist:

- Username: `admin`
- Password: `admin`

This is intended for local development bootstrap only. Change it before exposing the app to other users.

## Architecture

### Backend

- FastAPI application entry point: `backend/main.py`
- API routes: `backend/app/api/routes.py`
- PostgreSQL engine/session factory: `backend/app/database/engine.py`
- Scan persistence: `backend/app/database/db_store.py`
- User persistence: `backend/app/database/user_store.py`
- Password hashing and token signing: `backend/app/security/auth.py`

### Frontend

- Main app shell: `frontend/src/App.jsx`
- API client: `frontend/src/api/client.js`
- Login screen: `frontend/src/components/LoginPage.jsx`
- Scan history sidebar: `frontend/src/components/ScanSidebar.jsx`

## Requirements

### Core

- Python 3.12 recommended
- Node.js 20+ recommended
- npm
- PostgreSQL

### Python Dependencies

Backend Python dependencies are pinned in `backend/requirements.txt`.

### Native / OS Dependencies

- WeasyPrint needs native libraries for PDF generation
- `gobuster` is optional, but improves subdomain discovery on Kali/Parrot systems
- SecLists wordlists are optional, but required for Gobuster-based discovery

## Environment Variables

Create `backend/.env` from `backend/.env.example`.

Required values:

- `DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE`
- `APP_AUTH_SECRET=long_random_secret_for_signing_tokens`

Example:

```bash
cp backend/.env.example backend/.env
```

## Backend Setup

From the repo root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Start PostgreSQL and create a database/user that match your `DATABASE_URL`, then start the API:

```bash
uvicorn main:app --reload --port 8000
```

The backend listens on:

- `http://localhost:8000`

Useful endpoints:

- `GET /api/health`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/scan`
- `GET /api/scans`
- `GET /api/scan/{scan_id}`

## Frontend Setup

From the repo root:

```bash
cd frontend
npm install
npm run dev
```

The frontend listens on:

- `http://localhost:5173`

## Development Flow

1. Start PostgreSQL.
2. Start the backend from `backend/`.
3. Start the frontend from `frontend/`.
4. Open `http://localhost:5173`.
5. Sign in with `admin` / `admin`.
6. Launch a scan or reopen an existing one from the sidebar.

## Notes

- The backend seeds the default admin user at startup after ensuring tables exist.
- Passwords are stored as PBKDF2 hashes in the `users` table.
- Bearer tokens are signed with `APP_AUTH_SECRET`.
- `/api/health` is public, but scan and report endpoints require authentication.
- The frontend API base URL is currently hardcoded to `http://localhost:8000/api` in `frontend/src/api/client.js`.
