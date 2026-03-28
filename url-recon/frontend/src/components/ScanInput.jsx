/**
 * The domain input bar at the top of the page.
 * Handles its own local state for the input value.
 * Calls onScan(domain) when the user submits.
 * Shows a loading state while the scan is running.
 */
import { useState } from "react";

export default function ScanInput({ onScan, isScanning }) {
  const [domain, setDomain] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (!domain.trim()) return;
    onScan(domain.trim());
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-3">
      <input
        type="text"
        value={domain}
        onChange={(e) => setDomain(e.target.value)}
        placeholder="Enter domain — e.g. example.com or example.com/path"
        disabled={isScanning}
        className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-sm
                   focus:outline-none focus:ring-2 focus:ring-blue-500
                   disabled:bg-gray-50 disabled:text-gray-400"
      />
      <button
        type="submit"
        disabled={isScanning || !domain.trim()}
        className="px-5 py-2.5 bg-blue-600 text-white text-sm font-medium
                   rounded-lg hover:bg-blue-700 disabled:opacity-50
                   disabled:cursor-not-allowed transition-colors"
      >
        {isScanning ? "Scanning..." : "Scan"}
      </button>
    </form>
  );
}