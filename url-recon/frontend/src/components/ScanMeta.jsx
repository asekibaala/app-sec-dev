/**
 * Scan summary — ID, domain, duration, status.
 * First section the analyst sees after a scan completes.
 */
import SectionCard from "./SectionCard";

export default function ScanMeta({ meta }) {
  if (!meta) return null;
  return (
    <SectionCard title="Scan summary" status={meta.status === "complete" ? "PASS" : "WARN"}>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div><span className="text-gray-500 dark:text-slate-400">Domain</span><p className="font-medium dark:text-slate-100">{meta.domain}</p></div>
        <div><span className="text-gray-500 dark:text-slate-400">Duration</span><p className="font-medium dark:text-slate-100">{meta.duration_ms ? `${meta.duration_ms}ms` : "—"}</p></div>
        <div><span className="text-gray-500 dark:text-slate-400">Scan ID</span><p className="font-mono text-xs text-gray-600 dark:text-slate-300">{meta.id}</p></div>
        <div><span className="text-gray-500 dark:text-slate-400">Started</span><p className="font-medium dark:text-slate-100">{new Date(meta.started_at).toLocaleString()}</p></div>
      </div>
    </SectionCard>
  );
}
