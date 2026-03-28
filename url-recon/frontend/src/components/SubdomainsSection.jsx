/**
 * Discovered subdomains table.
 * Shows name, resolved IP, and a note when no IP was found.
 * Subdomains without IPs are still shown — they exist in CT
 * logs or DNS but may be dormant, which is still useful intel.
 */
import SectionCard from "./SectionCard";

export default function SubdomainsSection({ subdomains }) {
  if (!subdomains) return null;
  return (
    <SectionCard title={`Subdomains — ${subdomains.total} found`}>
      {subdomains.total === 0
        ? <p className="text-sm text-gray-500">No subdomains discovered.</p>
        : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">Subdomain</th>
                  <th className="text-left py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">IP address</th>
                </tr>
              </thead>
              <tbody>
                {subdomains.subdomains.map((s) => (
                  <tr key={s.name} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                    <td className="py-2 font-mono text-xs text-gray-800">{s.name}</td>
                    <td className="py-2 font-mono text-xs text-gray-500">{s.ip || <span className="text-gray-300">no A record</span>}</td>
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