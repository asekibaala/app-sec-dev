# Frontend Notes

This frontend is the authenticated client for Bugbounty hut.

## Current Behavior

- Starts on a login screen
- Authenticates against `POST /api/auth/login`
- Restores sessions with `GET /api/auth/me`
- Stores the bearer token in browser local storage
- Shows named scans in a history sidebar
- Downloads reports through authenticated fetch requests

## Important Files

- `src/App.jsx`
- `src/api/client.js`
- `src/components/LoginPage.jsx`
- `src/components/ScanInput.jsx`
- `src/components/ScanSidebar.jsx`
- `src/components/ReportDownloads.jsx`

## Expected Backend

The frontend expects the backend API at `http://localhost:8000/api`.

## Default Local Login

- Username: `admin`
- Password: `admin`

Full setup instructions live in `../README.md`.
