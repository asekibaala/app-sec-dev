/**
 * SSL/TLS certificate analysis.
 * The grade badge is the most prominent element —
 * it's the first thing the analyst's eye should land on.
 */
import SectionCard from "./SectionCard";

export default function SslSection({ ssl }) {
  if (!ssl) return null;
  return (
    <SectionCard title="SSL / TLS certificate" status={ssl.grade}>
      {ssl.error
        ? <p className="text-sm text-red-600 dark:text-red-300">{ssl.error}</p>
        : (
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div><span className="text-gray-500 dark:text-slate-400">Issuer</span><p className="font-medium dark:text-slate-100">{ssl.issuer || "—"}</p></div>
            <div><span className="text-gray-500 dark:text-slate-400">Subject</span><p className="font-medium dark:text-slate-100">{ssl.subject || "—"}</p></div>
            <div><span className="text-gray-500 dark:text-slate-400">Expiry date</span><p className="font-medium dark:text-slate-100">{ssl.expiry_date || "—"}</p></div>
            <div><span className="text-gray-500 dark:text-slate-400">Days remaining</span>
              <p className={`font-medium ${ssl.expiry_days < 30 ? "text-red-600 dark:text-red-300" : "text-green-600 dark:text-green-300"}`}>
                {ssl.expiry_days ?? "—"}
              </p>
            </div>
            <div><span className="text-gray-500 dark:text-slate-400">Self-signed</span><p className="font-medium dark:text-slate-100">{ssl.self_signed ? "Yes" : "No"}</p></div>
            <div>
              <span className="text-gray-500 dark:text-slate-400">Protocols</span>
              <div className="flex gap-1 mt-1 flex-wrap">
                {ssl.protocols?.map((p) => (
                  <span key={p} className={`text-xs px-2 py-0.5 rounded font-mono border
                    ${p === "TLSv1.3" ? "bg-green-50 text-green-700 border-green-200 dark:bg-green-950/40 dark:text-green-300 dark:border-green-900/50" :
                      p === "TLSv1.2" ? "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-900/50" :
                      "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-900/50"}`}>
                    {p}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )
      }
    </SectionCard>
  );
}
