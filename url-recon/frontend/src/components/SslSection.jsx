/**
 * SSL/TLS certificate analysis.
 * The grade badge is the most prominent element —
 * it's the first thing the analyst's eye should land on.
 */
import SectionCard from "./SectionCard";
import Badge from "./Badge";

export default function SslSection({ ssl }) {
  if (!ssl) return null;
  return (
    <SectionCard title="SSL / TLS certificate" status={ssl.grade}>
      {ssl.error
        ? <p className="text-sm text-red-600">{ssl.error}</p>
        : (
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div><span className="text-gray-500">Issuer</span><p className="font-medium">{ssl.issuer || "—"}</p></div>
            <div><span className="text-gray-500">Subject</span><p className="font-medium">{ssl.subject || "—"}</p></div>
            <div><span className="text-gray-500">Expiry date</span><p className="font-medium">{ssl.expiry_date || "—"}</p></div>
            <div><span className="text-gray-500">Days remaining</span>
              <p className={`font-medium ${ssl.expiry_days < 30 ? "text-red-600" : "text-green-600"}`}>
                {ssl.expiry_days ?? "—"}
              </p>
            </div>
            <div><span className="text-gray-500">Self-signed</span><p className="font-medium">{ssl.self_signed ? "Yes" : "No"}</p></div>
            <div>
              <span className="text-gray-500">Protocols</span>
              <div className="flex gap-1 mt-1 flex-wrap">
                {ssl.protocols?.map((p) => (
                  <span key={p} className={`text-xs px-2 py-0.5 rounded font-mono border
                    ${p === "TLSv1.3" ? "bg-green-50 text-green-700 border-green-200" :
                      p === "TLSv1.2" ? "bg-blue-50 text-blue-700 border-blue-200" :
                      "bg-red-50 text-red-700 border-red-200"}`}>
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