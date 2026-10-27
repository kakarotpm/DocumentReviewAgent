// Pieces shared by the Dashboard and Usage Analytics charts: stat cards, tooltip, table view, loading/empty states.
import { ErrorMessage, Spinner } from "./ui";

export function StatCard({ label, value, hint }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-slate-50">{value ?? "—"}</p>
      {hint && <p className="mt-0.5 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

// Tooltip box shared by every chart; text uses text colours, never series colours.
export function ChartTooltip({ active, payload, label, labelFormatter, valueFormatter, unit = "" }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-slate-200 bg-white px-3 py-2 text-xs shadow-md dark:border-slate-700 dark:bg-slate-900">
      <p className="mb-1 font-medium text-slate-900 dark:text-slate-100">{labelFormatter ? labelFormatter(label) : label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: p.color }} />
          {p.name}: <strong className="text-slate-900 dark:text-slate-100">{valueFormatter ? valueFormatter(p.value) : <>{p.value ?? "—"}{p.value != null && unit}</>}</strong>
        </p>
      ))}
    </div>
  );
}

// Every chart can also be read as a table (for screen readers, printing, or exact numbers).
export function DataTable({ columns, rows }) {
  return (
    <details className="mt-3 text-sm">
      <summary className="cursor-pointer text-xs font-medium text-slate-500 hover:text-slate-800 dark:hover:text-slate-200">View as table</summary>
      <table className="mt-2 w-full text-left">
        <thead className="text-xs text-slate-500">
          <tr>{columns.map((c) => <th key={c.key} className="py-1 pr-3 font-medium">{c.label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-t border-slate-100 dark:border-slate-800">
              {columns.map((c) => <td key={c.key} className="py-1 pr-3">{row[c.key] ?? "—"}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </details>
  );
}

export function ChartState({ query, empty, emptyText = "No completed reviews match these filters.", children }) {
  if (query.loading && !query.data) return <Spinner />;
  if (query.error) return <ErrorMessage error={query.error} onRetry={query.reload} />;
  if (empty) return <p className="py-10 text-center text-sm text-slate-500">{emptyText}</p>;
  return children;
}

export function axisProps(colors) {
  return { stroke: colors.axis, tick: { fill: colors.axis, fontSize: 12 }, tickLine: false, axisLine: { stroke: colors.grid } };
}
