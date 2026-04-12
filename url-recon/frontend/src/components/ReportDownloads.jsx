import { getStoredToken } from "../api/client";

const BASE_URL = "http://localhost:8000/api";

/**
 * Download a protected report by sending the bearer token manually, then
 * streaming the response into a browser download.
 */
async function downloadProtectedReport(scanId, format) {
  const token = getStoredToken();
  const response = await fetch(`${BASE_URL}/scan/${scanId}/report/${format}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!response.ok) {
    throw new Error(`Failed to download ${format.toUpperCase()} report.`);
  }

  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = downloadUrl;
  anchor.download = `recon-${scanId}.${format}`;
  anchor.click();
  window.URL.revokeObjectURL(downloadUrl);
}

/**
 * Download buttons shown after a scan completes.
 * Reports now travel through authenticated fetch requests instead of plain links.
 */
export default function ReportDownloads({ scanId }) {
  if (!scanId) return null;

  return (
    <div className="mb-6 flex flex-wrap gap-3">
      <button
        type="button"
        onClick={() => downloadProtectedReport(scanId, "html")}
        className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
      >
        Download HTML report
      </button>
      <button
        type="button"
        onClick={() => downloadProtectedReport(scanId, "pdf")}
        className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
      >
        Download PDF report
      </button>
    </div>
  );
}
