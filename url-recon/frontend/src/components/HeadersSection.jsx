/**
 * HTTP security headers analysis.
 * Each finding shows the header name, severity badge,
 * the actual value if present, and the analyst message.
 * Sorted so FAIL findings appear first — highest priority first.
 */
import SectionCard from "./SectionCard";
import Badge from "./Badge";

const SEVERITY_ORDER = { FAIL: 0, WARN: 1, INFO: 2, PASS: 3 };

export default function HeadersSection({ headers }) {
  if (!headers) return null;

  const sorted = [...(headers.findings || [])].sort(
    (a, b) => SEVERITY_ORDER[a.status] - SEVERITY_ORDER[b.status]
  );

  return (
    <SectionCard title="HTTP security headers">
      {headers.error
        ? <p className="text-sm text-red-600 dark:text-red-300">{headers.error}</p>
        : (
          <div className="flex flex-col gap-2">
            {sorted.map((f) => (
              <div key={f.header} className="flex items-start gap-3 py-2
                border-b border-gray-100 last:border-0 dark:border-slate-800">
                <div className="pt-0.5"><Badge status={f.status} /></div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-mono font-medium text-gray-800 dark:text-slate-100">{f.header}</p>
                  <p className="mt-0.5 text-xs text-gray-500 dark:text-slate-400">{f.message}</p>
                  {f.value && (
                    <p className="mt-0.5 truncate text-xs font-mono text-gray-400 dark:text-slate-500">{f.value}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )
      }
    </SectionCard>
  );
}
