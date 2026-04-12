// Base URL of the FastAPI backend.
// During development Vite runs on 5173, FastAPI on 8000.
const BASE_URL = "http://localhost:8000/api";
const AUTH_TOKEN_KEY = "url-recon-auth-token";

/**
 * Read the saved bearer token from localStorage.
 * Keeping this in one helper avoids repeating the storage key.
 */
export function getStoredToken() {
  return window.localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * Save or clear the bearer token used for authenticated API requests.
 */
export function setStoredToken(token) {
  if (token) {
    window.localStorage.setItem(AUTH_TOKEN_KEY, token);
    return;
  }
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
}

/**
 * Convert a failed fetch Response into a normal Error with a useful message.
 * We also attach the HTTP status so the UI can react to 401s cleanly.
 */
async function buildApiError(response, fallbackMessage) {
  let message = fallbackMessage;

  try {
    const data = await response.json();
    if (typeof data?.detail === "string" && data.detail.trim()) {
      message = data.detail;
    } else if (typeof data?.error === "string" && data.error.trim()) {
      message = data.error;
    }
  } catch {
    // Ignore JSON parse errors and keep the fallback message.
  }

  const error = new Error(message);
  error.status = response.status;
  return error;
}

/**
 * Shared fetch wrapper that automatically attaches the bearer token when present.
 */
async function apiRequest(path, options = {}) {
  const token = getStoredToken();
  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    throw await buildApiError(response, "Request failed");
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

/**
 * Authenticate a user and persist the returned bearer token locally.
 */
export async function login(username, password) {
  const data = await apiRequest("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  setStoredToken(data.access_token);
  return data;
}

/**
 * Fetch the currently authenticated user from the API.
 * Used to restore a session when the page refreshes.
 */
export function getCurrentUser() {
  return apiRequest("/auth/me");
}

/**
 * Remove the local token and end the frontend session.
 */
export function logout() {
  setStoredToken(null);
}

/**
 * Triggers a new domain scan.
 * Returns immediately with a scan_id — the scan runs in the background.
 * The caller uses the scan_id to poll for results.
 */
export function startScan(scanName, domain) {
  return apiRequest("/scan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scan_name: scanName, domain }),
  });
}

/**
 * Fetches the current state of a scan by its ID.
 * Returns partial results if the scan is still running.
 * Returns the full ScanResult when status is 'complete'.
 */
export function getScan(scanId) {
  return apiRequest(`/scan/${scanId}`);
}

/**
 * Returns a lightweight list of all past scans — meta only.
 * Used to populate the scan history sidebar.
 */
export function listScans() {
  return apiRequest("/scans");
}
