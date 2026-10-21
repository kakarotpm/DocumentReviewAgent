// Read-only view of a rulebook's rules.
import { CriticalBadge, WeightBadge } from "./ui";

export default function RuleList({ rules }) {
  return (
    <ol className="space-y-3">
      {rules.map((rule) => (
        <li key={rule.id} className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs text-slate-500">{rule.id}</span>
            <h3 className="font-medium text-slate-900 dark:text-slate-100">{rule.title}</h3>
            <span className="ml-auto flex flex-wrap gap-1.5">
              {rule.critical && <CriticalBadge />}
              <WeightBadge weight={rule.weight} />
            </span>
          </div>
          <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">{rule.check}</p>
          {(rule.pass_example || rule.fail_example) && (
            <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
              {rule.pass_example && (
                <div className="rounded-md bg-emerald-50 p-2 dark:bg-emerald-950/30">
                  <dt className="text-xs font-medium text-emerald-800 dark:text-emerald-300">✓ Passes</dt>
                  <dd className="text-slate-700 dark:text-slate-300">{rule.pass_example}</dd>
                </div>
              )}
              {rule.fail_example && (
                <div className="rounded-md bg-red-50 p-2 dark:bg-red-950/30">
                  <dt className="text-xs font-medium text-red-800 dark:text-red-300">✗ Fails</dt>
                  <dd className="text-slate-700 dark:text-slate-300">{rule.fail_example}</dd>
                </div>
              )}
            </dl>
          )}
        </li>
      ))}
    </ol>
  );
}
