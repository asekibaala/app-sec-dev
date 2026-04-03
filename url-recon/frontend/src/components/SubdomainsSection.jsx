/**
 * Discovered subdomains table.
 * Shows name, resolved IP, and a note when no IP was found.
 * Subdomains without IPs are still shown — they exist in CT
 * logs or DNS but may be dormant, which is still useful intel.
 */
import SectionCard from "./SectionCard";

export default function SubdomainsSection({ subdomains }) {
  if (!subdomains) return null;

  const visibleSubdomains = subdomains.subdomains.slice(0, 50);
  const remainingCount = Math.max(subdomains.total - visibleSubdomains.length, 0);

  return (
    <SectionCard title={`Subdomains — ${subdomains.total} found`}>
      {subdomains.total === 0
        ? <p className="text-sm text-gray-500 dark:text-slate-400">No subdomains discovered.</p>
        : (
          <div className="overflow-x-auto">
            <div className="mb-3 flex items-center justify-between gap-3 text-xs text-gray-500 dark:text-slate-400">
              <span>Showing the first {visibleSubdomains.length} subdomains.</span>
              {remainingCount > 0 && (
                <span>{remainingCount} more retained in scan results for reports/export.</span>
              )}
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-slate-800">
                  <th className="py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-slate-400">Subdomain</th>
                  <th className="py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-slate-400">IP address</th>
                </tr>
              </thead>
              <tbody>
                {visibleSubdomains.map((s) => (
                  <tr key={s.name} className="border-b border-gray-100 last:border-0 hover:bg-gray-50 dark:border-slate-800 dark:hover:bg-slate-800/60">
                    <td className="py-2 font-mono text-xs text-gray-800 dark:text-slate-100">{s.name}</td>
                    <td className="py-2 font-mono text-xs text-gray-500 dark:text-slate-400">{s.ip || <span className="text-gray-300 dark:text-slate-600">no A record</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      }
    </SectionCard>
  );
}
