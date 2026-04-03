/**
 * WHOIS registration data.
 * Shows registrar, creation, expiry and nameservers.
 */
import SectionCard from "./SectionCard";

export default function WhoisSection({ whois }) {
  if (!whois) return null;
  if (whois.error) return (
    <SectionCard title="WHOIS">
      <p className="text-sm text-red-600 dark:text-red-300">{whois.error}</p>
    </SectionCard>
  );
  return (
    <SectionCard title="WHOIS registration">
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div><span className="text-gray-500 dark:text-slate-400">Registrar</span><p className="font-medium dark:text-slate-100">{whois.registrar || "—"}</p></div>
        <div><span className="text-gray-500 dark:text-slate-400">Created</span><p className="font-medium dark:text-slate-100">{whois.created || "—"}</p></div>
        <div><span className="text-gray-500 dark:text-slate-400">Expires</span><p className="font-medium dark:text-slate-100">{whois.expires || "—"}</p></div>
        <div><span className="text-gray-500 dark:text-slate-400">Updated</span><p className="font-medium dark:text-slate-100">{whois.updated || "—"}</p></div>
      </div>
      {whois.nameservers?.length > 0 && (
        <div className="mt-3">
          <span className="text-xs uppercase tracking-wide text-gray-500 dark:text-slate-400">Nameservers</span>
          <div className="flex flex-wrap gap-2 mt-1">
            {whois.nameservers.map((ns) => (
              <span key={ns} className="rounded bg-gray-100 px-2 py-1 font-mono text-xs text-gray-700 dark:bg-slate-800 dark:text-slate-200">{ns}</span>
            ))}
          </div>
        </div>
      )}
    </SectionCard>
  );
}
