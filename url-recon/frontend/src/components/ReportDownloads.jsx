/**
 * Download buttons shown after a scan completes.
 * Calls the API report endpoints directly via anchor tags —
 * the browser handles the file download natively.
 * Only rendered when the scan status is 'complete'.
 */
const BASE_URL = "http://localhost:8000/api";

export default function ReportDownloads({ scanId }) {
  if (!scanId) return null;
  return (
    <div className="mb-6 flex flex-wrap gap-3">
      <a
        href={`${BASE_URL}/scan/${scanId}/report/html`}
        target="_blank"
        rel="noreferrer"
        className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
      >
        Download HTML report
      </a>
      <a
        href={`${BASE_URL}/scan/${scanId}/report/pdf`}
        target="_blank"
        rel="noreferrer"
        className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
      >
        Download PDF report
      </a>
    </div>
  );
}
