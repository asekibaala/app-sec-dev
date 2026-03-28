/**
 * Wrapper card for every results section.
 * Provides consistent padding, border, and heading style.
 * 'status' is optional — shows a badge next to the title
 * for sections that have a single top-level grade (SSL).
 */
import Badge from "./Badge";

export default function SectionCard({ title, status, children }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 mb-4">
      <div className="flex items-center gap-3 mb-4">
        <h2 className="text-base font-semibold text-gray-900">{title}</h2>
        {status && <Badge status={status} />}
      </div>
      {children}
    </div>
  );
}