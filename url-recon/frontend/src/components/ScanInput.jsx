/**
 * The domain input bar at the top of the page.
 * Handles its own local state for the input value.
 * Calls onScan({ scanName, domain }) when the user submits.
 * Shows a loading state while the scan is running.
 */
import { useState } from "react";

function preValidate(scanName, domain) {
  if (!scanName.trim()) return "Please enter a scan name.";
  if (scanName.trim().length > 80) return "Scan name is too long.";
  if (!domain.trim()) return "Please enter a domain name.";
  if (domain.includes(" ")) return "Domain cannot contain spaces.";
  if (/^https?:\/\//i.test(domain)) return null;
  if (!domain.includes(".")) return "Domain must include a TLD — e.g. example.com";
  if (domain.length > 253) return "Domain is too long.";
  return null;
}

export default function ScanInput({ onScan, isScanning }) {
  const [scanName, setScanName] = useState("");
  const [domain, setDomain] = useState("");
  const [validationError, setValidationError] = useState(null);

  function handleSubmit(e) {
    e.preventDefault();
    const error = preValidate(scanName, domain);
    setValidationError(error);
    if (error || !domain.trim()) return;
    onScan({ scanName: scanName.trim(), domain: domain.trim() });
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="grid gap-3 md:grid-cols-[1fr_1.2fr_auto]">
        <input
          type="text"
          value={scanName}
          onChange={(e) => {
            setScanName(e.target.value);
            if (validationError) {
              setValidationError(preValidate(e.target.value, domain));
            }
          }}
          placeholder="Name this scan — e.g. April external review"
          disabled={isScanning}
          className="rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-400 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500 dark:disabled:bg-slate-800 dark:disabled:text-slate-500"
        />
        <input
          type="text"
          value={domain}
          onChange={(e) => {
            setDomain(e.target.value);
            if (validationError) {
              setValidationError(preValidate(scanName, e.target.value));
            }
          }}
          placeholder="Enter domain — e.g. example.com or example.com/path"
          disabled={isScanning}
          className="rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-400 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500 dark:disabled:bg-slate-800 dark:disabled:text-slate-500"
        />
        <button
          type="submit"
          disabled={isScanning || !scanName.trim() || !domain.trim()}
          className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isScanning ? "Scanning..." : "Scan"}
        </button>
      </form>

      {validationError && (
        <p className="mt-2 text-sm text-red-600 dark:text-red-400">{validationError}</p>
      )}
    </div>
  );
}
