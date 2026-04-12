import { useEffect, useRef, useState } from "react";

import {
  getCurrentUser,
  getScan,
  listScans,
  login,
  logout,
  startScan,
} from "./api/client";
import DnsSection from "./components/DnsSection";
import HeadersSection from "./components/HeadersSection";
import LoginPage from "./components/LoginPage";
import ReportDownloads from "./components/ReportDownloads";
import ScanInput from "./components/ScanInput";
import ScanMeta from "./components/ScanMeta";
import ScanSidebar from "./components/ScanSidebar";
import SslSection from "./components/SslSection";
import SubdomainsSection from "./components/SubdomainsSection";
import WhoisSection from "./components/WhoisSection";

function getInitialTheme() {
  if (typeof window === "undefined") return "light";

  const storedTheme = window.localStorage.getItem("theme");
  if (storedTheme === "light" || storedTheme === "dark") return storedTheme;

  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

/**
 * Main authenticated application shell.
 * It either renders the login screen or the protected scanning workspace.
 */
export default function App() {
  const [result, setResult] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const [theme, setTheme] = useState(getInitialTheme);
  const [user, setUser] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [authError, setAuthError] = useState(null);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [selectedScanId, setSelectedScanId] = useState(null);
  const [isLoadingScan, setIsLoadingScan] = useState(false);
  const pollRef = useRef(null);

  /**
   * Clear the client-side session and return to the login view.
   * We also stop any active polling loop because it no longer has a valid token.
   */
  function clearSession(message = null) {
    clearInterval(pollRef.current);
    pollRef.current = null;
    logout();
    setUser(null);
    setHistory([]);
    setResult(null);
    setSelectedScanId(null);
    setIsScanning(false);
    setIsLoadingScan(false);
    setError(null);
    setAuthError(message);
  }

  /**
   * Centralise API error handling so 401 responses consistently log the user out.
   */
  function handleApiError(apiError, fallbackMessage) {
    if (apiError?.status === 401) {
      clearSession("Your session expired. Please log in again.");
      return true;
    }

    setError(apiError?.message || fallbackMessage);
    return false;
  }

  /**
   * Fetch the scan history shown in the left sidebar.
   * When possible we keep the current selection stable.
   */
  async function refreshHistory(preferredScanId = null) {
    const data = await listScans();
    const scans = data.scans || [];
    setHistory(scans);

    const nextSelectedId =
      preferredScanId ||
      (scans.some((scan) => scan.id === selectedScanId) ? selectedScanId : scans[0]?.id || null);

    setSelectedScanId(nextSelectedId);
    return { scans, nextSelectedId };
  }

  /**
   * Load one scan from the API and show it in the main results panel.
   */
  async function loadScanById(scanId) {
    if (!scanId) {
      setSelectedScanId(null);
      setResult(null);
      return;
    }

    setIsLoadingScan(true);
    setError(null);
    setSelectedScanId(scanId);

    try {
      const data = await getScan(scanId);
      setResult(data);
    } catch (apiError) {
      if (!handleApiError(apiError, "Failed to fetch scan results.")) {
        setResult(null);
      }
    } finally {
      setIsLoadingScan(false);
    }
  }

  /**
   * Restore a saved session when the page refreshes.
   */
  useEffect(() => {
    let cancelled = false;

    async function bootstrapSession() {
      try {
        const currentUser = await getCurrentUser();
        if (cancelled) return;

        setUser(currentUser);
        setAuthError(null);

        const { nextSelectedId } = await refreshHistory();
        if (!cancelled && nextSelectedId) {
          await loadScanById(nextSelectedId);
        }
      } catch (apiError) {
        if (!cancelled && apiError?.status === 401) {
          logout();
        } else if (!cancelled) {
          setAuthError(apiError?.message || "Failed to restore session.");
        }
      } finally {
        if (!cancelled) {
          setAuthChecked(true);
        }
      }
    }

    bootstrapSession();
    return () => {
      cancelled = true;
    };
  }, []);

  /**
   * Keep the selected theme mirrored on the root element and in localStorage.
   */
  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    window.localStorage.setItem("theme", theme);
  }, [theme]);

  /**
   * Clean up any outstanding polling timer when the component unmounts.
   */
  useEffect(() => () => clearInterval(pollRef.current), []);

  async function handleLogin(username, password) {
    setIsAuthenticating(true);
    setAuthError(null);

    try {
      const session = await login(username, password);
      setUser({ username: session.username });

      const { nextSelectedId } = await refreshHistory();
      if (nextSelectedId) {
        await loadScanById(nextSelectedId);
      } else {
        setResult(null);
      }
    } catch (apiError) {
      setAuthError(apiError?.message || "Login failed.");
    } finally {
      setIsAuthenticating(false);
      setAuthChecked(true);
    }
  }

  async function handleScan({ scanName, domain }) {
    clearInterval(pollRef.current);
    pollRef.current = null;
    setError(null);
    setResult(null);
    setIsScanning(true);

    try {
      const { scan_id } = await startScan(scanName, domain);
      setSelectedScanId(scan_id);

      pollRef.current = setInterval(async () => {
        try {
          const data = await getScan(scan_id);
          setResult(data);
          setSelectedScanId(scan_id);

          if (data.meta.status === "complete" || data.meta.status === "failed") {
            clearInterval(pollRef.current);
            pollRef.current = null;
            setIsScanning(false);
            await refreshHistory(scan_id);
          }
        } catch (apiError) {
          clearInterval(pollRef.current);
          pollRef.current = null;
          setIsScanning(false);
          handleApiError(apiError, "Failed to fetch scan results.");
        }
      }, 2000);

      await refreshHistory(scan_id);
    } catch (apiError) {
      setIsScanning(false);
      handleApiError(apiError, "Failed to start scan.");
    }
  }

  async function handleSelectScan(scanId) {
    clearInterval(pollRef.current);
    pollRef.current = null;
    setIsScanning(false);
    await loadScanById(scanId);
  }

  function handleStartNewScan() {
    clearInterval(pollRef.current);
    pollRef.current = null;
    setIsScanning(false);
    setError(null);
    setResult(null);
    setSelectedScanId(null);
  }

  function toggleTheme() {
    setTheme((currentTheme) => (currentTheme === "dark" ? "light" : "dark"));
  }

  if (!authChecked || !user) {
    return (
      <LoginPage
        onLogin={handleLogin}
        isSubmitting={isAuthenticating || !authChecked}
        error={authError}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 transition-colors dark:bg-slate-950 dark:text-slate-100">
      <header className="border-b border-gray-200 bg-white px-6 py-4 dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-slate-100">Bugbounty hut</h1>
            <p className="mt-0.5 text-xs text-gray-500 dark:text-slate-400">
              Authenticated as {user.username}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
              className="inline-flex items-center rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              {theme === "dark" ? "Light mode" : "Dark mode"}
            </button>
            <button
              type="button"
              onClick={() => clearSession()}
              className="inline-flex items-center rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 px-6 py-6 lg:grid-cols-[320px_minmax(0,1fr)]">
        <ScanSidebar
          scans={history}
          selectedScanId={selectedScanId}
          onSelectScan={handleSelectScan}
          onStartNewScan={handleStartNewScan}
          isLoading={isLoadingScan}
        />

        <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="mb-6">
            <ScanInput onScan={handleScan} isScanning={isScanning} />
          </div>

          {isScanning && (
            <div className="mb-6 flex items-center gap-3 text-sm text-gray-500 dark:text-slate-400">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
              Running 5 intelligence modules in parallel...
            </div>
          )}

          {error && (
            <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300">
              {error}
            </div>
          )}

          <ReportDownloads scanId={result?.meta?.status === "complete" ? result.meta.id : null} />

          {isLoadingScan && (
            <div className="mb-6 rounded-2xl border border-gray-200 bg-gray-50 px-4 py-5 text-sm text-gray-500 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-400">
              Loading selected scan...
            </div>
          )}

          {result ? (
            <div>
              <ScanMeta meta={result.meta} />
              <SslSection ssl={result.ssl} />
              <HeadersSection headers={result.headers} />
              <WhoisSection whois={result.whois} />
              <DnsSection dns={result.dns} />
              <SubdomainsSection subdomains={result.subdomains} />
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-gray-200 bg-gray-50 px-5 py-10 text-sm text-gray-500 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-400">
              Select a previous scan from the sidebar or launch a new reconnaissance run.
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
