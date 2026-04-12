# Bugbounty hut

Bugbounty hut is a two-part reconnaissance application:

- A FastAPI backend that authenticates users, launches scans, stores results in PostgreSQL, and serves downloadable reports
- A React + Vite frontend that provides login, scan creation, history, and report access

## Current Authentication Stack

The backend now uses FastAPI Users for local authentication.

- Local auth backend: FastAPI Users + JWT bearer tokens
- Password hashing: framework-managed via `pwdlib` / Argon2-compatible hashing
- Protected routes: FastAPI Users current-user dependency
- Default bootstrap account: `admin` / `admin`

The bootstrap account is for local setup only. Change it before exposing the app to other users.

## Future Active Directory Provision

The auth configuration includes a reserved external identity-provider mode for a future secure Windows Active Directory integration.

- Current mode: `AUTH_PROVIDER_MODE=local`
- Planned enterprise path: OIDC federation through Entra ID, ADFS, or another OIDC bridge
- Deliberate design choice: prefer OIDC federation over raw LDAP password binds for stronger policy, MFA, and conditional-access support

Relevant files:

- `backend/app/auth/users.py`
- `backend/app/auth/schemas.py`
- `backend/app/auth/settings.py`

## Current Features

- Login page and authenticated session bootstrap
- Named scans with separate scan titles and target domains
- Scan history sidebar for reopening prior scans
- Per-domain cooldown: `60` seconds
- Per-IP rate limit: `10` requests per `60` seconds
- HTML and PDF reports for completed scans

## Environment Variables

Create `backend/.env` from `backend/.env.example`.

Required now:

- `DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE`
- `APP_AUTH_SECRET=long_random_secret`
- `AUTH_PROVIDER_MODE=local`

Reserved for future external OIDC auth:

- `OIDC_DISCOVERY_URL`
- `OIDC_CLIENT_ID`
- `OIDC_CLIENT_SECRET`
- `OIDC_SCOPES`

## Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The backend listens on `http://localhost:8000`.

Useful endpoints:

- `GET /api/health`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/scan`
- `GET /api/scans`
- `GET /api/scan/{scan_id}`

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the backend API at `http://localhost:8000/api`.

## Development Flow

1. Start PostgreSQL.
2. Start the backend from `backend/`.
3. Start the frontend from `frontend/`.
4. Open `http://localhost:5173`.
5. Sign in with `admin` / `admin`.
6. Create a named scan and review prior scans from the sidebar.
