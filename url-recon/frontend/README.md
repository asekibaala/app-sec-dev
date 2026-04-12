# Frontend Notes

This frontend is a React + Vite client for the authenticated URL Recon backend.

## What Changed

- The app now starts on a login page
- Successful login stores a bearer token in browser local storage
- The main workspace includes a scan-history sidebar for reopening prior scans
- Report downloads now use authenticated fetch requests instead of unauthenticated links

## Important Files

- App shell: `src/App.jsx`
- API client: `src/api/client.js`
- Login screen: `src/components/LoginPage.jsx`
- History sidebar: `src/components/ScanSidebar.jsx`
- Protected report downloads: `src/components/ReportDownloads.jsx`

## Expected Backend

The frontend expects the backend API at:

- `http://localhost:8000/api`

That base URL is currently hardcoded in:

- `src/api/client.js`

## Default Local Login

When the backend starts for the first time, it seeds:

- Username: `admin`
- Password: `admin`

Full setup instructions live in the repo root README:

- `../README.md`
