import { useState, useEffect, useRef } from "react";
import { startScan, getScan, listScans } from "./api/client";
import ScanInput from "./components/ScanInput";
import ScanMeta from "./components/ScanMeta";
import WhoisSection from "./components/WhoisSection";
import DnsSection from "./components/DnsSection";
import SslSection from "./components/SslSection";
import HeadersSection from "./components/HeadersSection";
import SubdomainsSection from "./components/SubdomainsSection";

export default function App() {
  // The current scan result — null until a scan completes
  const [result, setResult] = useState(null);
  // True while a scan is running — disables the input
  const [isScanning, setIsScanning] = useState(false);
  // Error message to show if the scan fails
  const [error, setError] = useState(null);
  // Past scans for the history sidebar
  const [history, setHistory] = useState([]);
  // We store the polling interval ref so we can cancel it
  const pollRef = useRef(null);

  // Load scan history on first render
  useEffect(() => {
    listScans()
      .then((data) => setHistory(data.scans || []))
      .catch(() => {});
  }, []);

  async function handleScan(domain) {
    // Reset state for the new scan
    setError(null);
    setResult(null);
    setIsScanning(true);

    try {
      // Trigger the scan — returns immediately with scan_id
      const { scan_id } = await startScan(domain);

      // Poll every 2 seconds until the scan is complete or failed
      pollRef.current = setInterval(async () => {
        try {
          const data = await getScan(scan_id);
          setResult(data);

          // Stop polling once the scan reaches a terminal state
          if (data.meta.status === "complete" || data.meta.status === "failed") {
            clearInterval(pollRef.current);
            setIsScanning(false);
            // Refresh scan history
            listScans().then((d) => setHistory(d.scans || []));
          }
        } catch (e) {
          clearInterval(pollRef.current);
          setIsScanning(false);
          setError("Failed to fetch scan results.");
        }
      }, 2000);

    } catch (e) {
      setIsScanning(false);
      setError("Failed to start scan. Is the API running?");
    }
  }

  // Clean up the polling interval when the component unmounts
  useEffect(() => () => clearInterval(pollRef.current), []);

  return (
    <div className="min-h-screen bg-gray-50">

      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-lg font-semibold text-gray-900">URL Recon</h1>
          <p className="text-xs text-gray-500 mt-0.5">Domain security intelligence</p>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-6">

        {/* Scan input */}
        <div className="mb-6">
          <ScanInput onScan={handleScan} isScanning={isScanning} />
        </div>

        {/* Scanning indicator */}
        {isScanning && (
          <div className="flex items-center gap-3 mb-6 text-sm text-gray-500">
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent
                            rounded-full animate-spin" />
            Running 5 intelligence modules in parallel...
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Results — render each section as data arrives */}
        {result && (
          <div>
            <ScanMeta       meta={result.meta} />
            <SslSection     ssl={result.ssl} />
            <HeadersSection headers={result.headers} />
            <WhoisSection   whois={result.whois} />
            <DnsSection     dns={result.dns} />
            <SubdomainsSection subdomains={result.subdomains} />
          </div>
        )}

        {/* Scan history */}
        {history.length > 0 && !result && (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-base font-semibold text-gray-900 mb-4">Recent scans</h2>
            <div className="flex flex-col gap-2">
              {history.map((scan) => (
                <div key={scan.id}
                  className="flex items-center justify-between py-2
                             border-b border-gray-100 last:border-0 text-sm">
                  <span className="font-medium text-gray-800">{scan.domain}</span>
                  <span className="text-xs text-gray-400">
                    {new Date(scan.started_at).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}