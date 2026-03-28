/**
 * DNS records — one row per record type.
 * Empty record types are shown as a dash, not hidden,
 * so the analyst can see what's missing as well as what's present.
 */
import SectionCard from "./SectionCard";

function RecordRow({ type, values }) {
  return (
    <div className="flex gap-4 py-2 border-b border-gray-100 last:border-0 text-sm">
      <span className="w-12 font-mono text-xs font-semibold text-blue-700 pt-0.5">{type}</span>
      <div className="flex flex-col gap-0.5">
        {values?.length > 0
          ? values.map((v) => <span key={v} className="text-gray-800 font-mono text-xs">{v}</span>)
          : <span className="text-gray-400 text-xs">—</span>
        }
      </div>
    </div>
  );
}

export default function DnsSection({ dns }) {
  if (!dns) return null;
  return (
    <SectionCard title="DNS records">
      <RecordRow type="A"    values={dns.A} />
      <RecordRow type="AAAA" values={dns.AAAA} />
      <RecordRow type="MX"   values={dns.MX} />
      <RecordRow type="NS"   values={dns.NS} />
      <RecordRow type="TXT"  values={dns.TXT} />
      {dns.SOA && <RecordRow type="SOA" values={[dns.SOA]} />}
    </SectionCard>
  );
}