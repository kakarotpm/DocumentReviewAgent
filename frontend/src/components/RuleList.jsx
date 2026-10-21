// Read-only list of rules. The rule definition ("what the reviewer checks") is the main thing;
// the pass/fail examples are secondary, so they're small, grey and folded away.
import { useState } from "react";
import Icon from "./Icon";
import { CriticalBadge, WeightBadge } from "./ui";

function Examples({ rule }) {
  const [open, setOpen] = useState(false);
  if (!rule.pass_example && !rule.fail_example) return null;
  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
        aria-expanded={open}
      >
        <Icon name="chevron" className={`h-3.5 w-3.5 transition-transform ${open ? "" : "-rotate-90"}`} />
        {open ? "Hide examples" : "Show examples"}
      </button>
      {open && (
        <dl className="mt-2 space-y-1.5 border-l-2 border-slate-200 pl-3 text-xs text-slate-500 dark:border-slate-700">
          {rule.pass_example && (
            <div>
              <dt className="inline font-medium">Passes: </dt>
              <dd className="inline">{rule.pass_example}</dd>
            </div>
          )}
          {rule.fail_example && (
            <div>
              <dt className="inline font-medium">Fails: </dt>
              <dd className="inline">{rule.fail_example}</dd>
            </div>
          )}
        </dl>
      )}
    </div>
  );
}

export function RuleCard({ rule, actions }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <header className="flex flex-wrap items-start gap-x-3 gap-y-2">
        <div className="min-w-0 flex-1">
          <p className="font-mono text-xs text-slate-400">{rule.id}</p>
          <h3 className="text-base font-semibold text-slate-900 dark:text-slate-50">{rule.title}</h3>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          {rule.critical && <CriticalBadge />}
          <WeightBadge weight={rule.weight} />
        </div>
      </header>
      <p className="mt-3 text-[15px] leading-relaxed text-slate-800 dark:text-slate-200">{rule.check}</p>
      <Examples rule={rule} />
      {actions && <footer className="mt-4 flex flex-wrap gap-1 border-t border-slate-100 pt-3 dark:border-slate-800">{actions}</footer>}
    </article>
  );
}

export default function RuleList({ rules, renderActions }) {
  return (
    <ol className="space-y-3">
      {rules.map((rule) => (
        <li key={rule.id}>
          <RuleCard rule={rule} actions={renderActions?.(rule)} />
        </li>
      ))}
    </ol>
  );
}
