/**
 * Severity badge — maps a status string to a color.
 * Used consistently across every results section.
 *
 * Status values and their meanings:
 *   PASS  — correctly configured, no action needed
 *   INFO  — worth noting, no immediate action needed
 *   WARN  — should be fixed, not critical
 *   FAIL  — needs immediate attention
 *   A+/A  — strong SSL grade
 *   B/C   — weak SSL grade
 *   F     — failing SSL grade
 */
const COLORS = {
  PASS:  "bg-green-100  text-green-800  border-green-200",
  INFO:  "bg-blue-100   text-blue-800   border-blue-200",
  WARN:  "bg-amber-100  text-amber-800  border-amber-200",
  FAIL:  "bg-red-100    text-red-800    border-red-200",
  "A+":  "bg-green-100  text-green-800  border-green-200",
  A:     "bg-green-100  text-green-800  border-green-200",
  B:     "bg-amber-100  text-amber-800  border-amber-200",
  C:     "bg-amber-100  text-amber-800  border-amber-200",
  F:     "bg-red-100    text-red-800    border-red-200",
};

export default function Badge({ status }) {
  const colors = COLORS[status] || "bg-gray-100 text-gray-800 border-gray-200";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${colors}`}>
      {status}
    </span>
  );
}