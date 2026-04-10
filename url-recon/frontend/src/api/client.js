// Base URL of the FastAPI backend.
// During development Vite runs on 5173, FastAPI on 8000.
const BASE_URL = "http://localhost:8000/api";

/**
 * Triggers a new domain scan.
 * Returns immediately with a scan_id — the scan runs in the background.
 * The caller uses the scan_id to poll for results.
 */
export async function startScan(domain) {
  const response = await fetch(`${BASE_URL}/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ domain }),
  });

  if (!response.ok) {
    let message = "Failed to start scan";

    try {
      const data = await response.json();
      if (typeof data?.detail === "string" && data.detail.trim()) {
        message = data.detail;
      } else if (typeof data?.error === "string" && data.error.trim()) {
        message = data.error;
      }
    } catch {
      // Fall back to the generic message when the response isn't JSON.
    }

    throw new Error(message);
  }

  return response.json();
}

/**
 * Fetches the current state of a scan by its ID.
 * Returns partial results if the scan is still running.
 * Returns the full ScanResult when status is 'complete'.
 */
export async function getScan(scanId) {
  const response = await fetch(`${BASE_URL}/scan/${scanId}`);
  if (!response.ok) throw new Error("Scan not found");
  return response.json();
}

/**
 * Returns a lightweight list of all past scans — meta only.
 * Used to populate the scan history sidebar.
 */
export async function listScans() {
  const response = await fetch(`${BASE_URL}/scans`);
  if (!response.ok) throw new Error("Failed to fetch scans");
  return response.json();
}
