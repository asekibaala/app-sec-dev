import { useState, useEffect, useRef } from "react";
import { startScan, getScan, listScans } from "./api/client";
import ScanInput from "./components/ScanInput";
import ScanMeta from "./components/ScanMeta";
import WhoisSection from "./components/WhoisSection";
import DnsSection from "./components/DnsSection";
import SslSection from "./components/SslSection";
import HeadersSection from "./components/HeadersSection";
import ReportDownloads from "./components/ReportDownloads";
import SubdomainsSection from "./components/SubdomainsSection";

function getInitialTheme() {
  if (typeof window === "undefined") return "light";

  const storedTheme = window.localStorage.getItem("theme");
  if (storedTheme === "light" || storedTheme === "dark") return storedTheme;

  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function App() {
  // The current scan result — null until a scan completes
  const [result, setResult] = useState(null);
  // True while a scan is running — disables the input
  const [isScanning, setIsScanning] = useState(false);
  // Error message to show if the scan fails
  const [error, setError] = useState(null);
  // Past scans for the history sidebar
  const [history, setHistory] = useState([]);
  const [theme, setTheme] = useState(getInitialTheme);
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

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    window.localStorage.setItem("theme", theme);
  }, [theme]);

  function toggleTheme() {
    setTheme((currentTheme) => currentTheme === "dark" ? "light" : "dark");
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 transition-colors dark:bg-slate-950 dark:text-slate-100">

      {/* Header */}
      <header className="border-b border-gray-200 bg-white px-6 py-4 dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4">
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-slate-100">URL Recon</h1>
            <p className="mt-0.5 text-xs text-gray-500 dark:text-slate-400">Domain security intelligence</p>
          </div>
          <button
            type="button"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            className="inline-flex items-center rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
          >
            {theme === "dark" ? "Light mode" : "Dark mode"}
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-6">

        {/* Scan input */}
        <div className="mb-6">
          <ScanInput onScan={handleScan} isScanning={isScanning} />
        </div>

        {/* Scanning indicator */}
        {isScanning && (
          <div className="mb-6 flex items-center gap-3 text-sm text-gray-500 dark:text-slate-400">
            <div className="h-4 w-4 rounded-full border-2 border-blue-500 border-t-transparent
                            rounded-full animate-spin" />
            Running 5 intelligence modules in parallel...
          </div>
        )}

        <ReportDownloads scanId={result?.meta?.status === "complete" ? result?.meta?.id : null} />

        {/* Error state */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300">
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
          <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
            <h2 className="mb-4 text-base font-semibold text-gray-900 dark:text-slate-100">Recent scans</h2>
            <div className="flex flex-col gap-2">
              {history.map((scan) => (
                <div key={scan.id}
                  className="flex items-center justify-between border-b border-gray-100 py-2 text-sm last:border-0 dark:border-slate-800">
                  <span className="font-medium text-gray-800 dark:text-slate-200">{scan.domain}</span>
                  <span className="text-xs text-gray-400 dark:text-slate-500">
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
