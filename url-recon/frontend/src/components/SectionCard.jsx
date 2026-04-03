/**
 * Wrapper card for every results section.
 * Provides consistent padding, border, and heading style.
 * 'status' is optional — shows a badge next to the title
 * for sections that have a single top-level grade (SSL).
 */
import Badge from "./Badge";

export default function SectionCard({ title, status, children }) {
  return (
    <div className="mb-4 rounded-lg border border-gray-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center gap-3 mb-4">
        <h2 className="text-base font-semibold text-gray-900 dark:text-slate-100">{title}</h2>
        {status && <Badge status={status} />}
      </div>
      {children}
    </div>
  );
}
