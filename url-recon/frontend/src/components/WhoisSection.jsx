/**
 * WHOIS registration data.
 * Shows registrar, creation, expiry and nameservers.
 */
import SectionCard from "./SectionCard";

export default function WhoisSection({ whois }) {
  if (!whois) return null;
  if (whois.error) return (
    <SectionCard title="WHOIS">
      <p className="text-sm text-red-600">{whois.error}</p>
    </SectionCard>
  );
  return (
    <SectionCard title="WHOIS registration">
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div><span className="text-gray-500">Registrar</span><p className="font-medium">{whois.registrar || "—"}</p></div>
        <div><span className="text-gray-500">Created</span><p className="font-medium">{whois.created || "—"}</p></div>
        <div><span className="text-gray-500">Expires</span><p className="font-medium">{whois.expires || "—"}</p></div>
        <div><span className="text-gray-500">Updated</span><p className="font-medium">{whois.updated || "—"}</p></div>
      </div>
      {whois.nameservers?.length > 0 && (
        <div className="mt-3">
          <span className="text-xs text-gray-500 uppercase tracking-wide">Nameservers</span>
          <div className="flex flex-wrap gap-2 mt-1">
            {whois.nameservers.map((ns) => (
              <span key={ns} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded font-mono">{ns}</span>
            ))}
          </div>
        </div>
      )}
    </SectionCard>
  );
}