function formatScanTimestamp(value) {
  if (!value) return "Unknown time";
  return new Date(value).toLocaleString();
}

/**
 * Sidebar navigation for existing scans.
 * Selecting an item loads the full scan into the main content area.
 */
export default function ScanSidebar({
  scans,
  selectedScanId,
  onSelectScan,
  onStartNewScan,
  isLoading,
}) {
  return (
    <aside className="rounded-3xl border border-gray-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between gap-3 border-b border-gray-100 pb-4 dark:border-slate-800">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-gray-500 dark:text-slate-500">
            History
          </p>
          <h2 className="mt-1 text-lg font-semibold text-gray-900 dark:text-slate-100">
            Previous scans
          </h2>
        </div>
        <button
          type="button"
          onClick={onStartNewScan}
          className="rounded-xl border border-gray-200 px-3 py-2 text-xs font-semibold text-gray-700 transition hover:bg-gray-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          New scan
        </button>
      </div>

      <div className="mt-4 flex max-h-[70vh] flex-col gap-2 overflow-y-auto pr-1">
        {scans.length === 0 && (
          <div className="rounded-2xl border border-dashed border-gray-200 px-4 py-5 text-sm text-gray-500 dark:border-slate-700 dark:text-slate-400">
            No scans yet. Launch your first scan from the main panel.
          </div>
        )}

        {scans.map((scan) => {
          const isSelected = scan.id === selectedScanId;

          return (
            <button
              key={scan.id}
              type="button"
              onClick={() => onSelectScan(scan.id)}
              disabled={isLoading}
              className={`rounded-2xl border px-4 py-3 text-left transition ${
                isSelected
                  ? "border-blue-500 bg-blue-50 dark:border-blue-500 dark:bg-blue-950/40"
                  : "border-gray-200 bg-gray-50 hover:bg-gray-100 dark:border-slate-800 dark:bg-slate-950 dark:hover:bg-slate-800"
              }`}
            >
              <div>
                <p className="text-sm font-semibold text-gray-900 dark:text-slate-100">
                  {scan.scan_name || scan.domain}
                </p>
                <span
                  className={`mt-2 inline-flex rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] ${
                    scan.status === "complete"
                      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300"
                      : scan.status === "failed"
                        ? "bg-red-100 text-red-700 dark:bg-red-950/50 dark:text-red-300"
                        : "bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300"
                  }`}
                >
                  {scan.status}
                </span>
                <p className="mt-2 text-xs text-gray-600 dark:text-slate-300">
                  {scan.domain}
                </p>
                <p className="mt-1 text-xs text-gray-500 dark:text-slate-400">
                  {formatScanTimestamp(scan.started_at)}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </aside>
  );
}
