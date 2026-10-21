// Shared building blocks so every page looks and behaves the same.
import { Link } from "react-router-dom";
import Icon from "./Icon";

const BUTTON_STYLES = {
  primary: "bg-indigo-600 text-white hover:bg-indigo-700 disabled:bg-indigo-300 dark:disabled:bg-indigo-900 dark:disabled:text-indigo-400",
  secondary:
    "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800",
  danger: "text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/50",
  ghost: "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800",
};

export function Button({ variant = "primary", icon, children, className = "", to, ...props }) {
  const classes = `inline-flex items-center justify-center gap-2 rounded-md px-3.5 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed ${BUTTON_STYLES[variant]} ${className}`;
  const content = (
    <>
      {icon && <Icon name={icon} />}
      {children}
    </>
  );
  if (to) {
    return (
      <Link to={to} className={classes}>
        {content}
      </Link>
    );
  }
  return (
    <button type="button" className={classes} {...props}>
      {content}
    </button>
  );
}

export function Card({ children, className = "", title, actions }) {
  return (
    <section className={`rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900 ${className}`}>
      {(title || actions) && (
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          {title && <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">{title}</h2>}
          {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  );
}

export function PageHeader({ title, subtitle, actions, back }) {
  return (
    <header className="mb-6">
      {back && (
        <Link to={back.to} className="mb-3 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800 dark:hover:text-slate-200">
          <Icon name="arrow-left" /> {back.label}
        </Link>
      )}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">{title}</h1>
          {subtitle && <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">{subtitle}</div>}
        </div>
        {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
      </div>
    </header>
  );
}

export function Field({ label, hint, children, required }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
        {label} {required && <span className="text-red-600">*</span>}
      </span>
      {children}
      {hint && <span className="mt-1 block text-xs text-slate-500">{hint}</span>}
    </label>
  );
}

export function Spinner({ label = "Loading…" }) {
  return (
    <div className="flex items-center gap-3 py-10 text-sm text-slate-500" role="status">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600" />
      {label}
    </div>
  );
}

export function EmptyState({ icon = "folder", title, children, action }) {
  return (
    <div className="flex flex-col items-center rounded-xl border border-dashed border-slate-300 px-6 py-12 text-center dark:border-slate-700">
      <Icon name={icon} className="h-8 w-8 text-slate-400" />
      <h3 className="mt-3 font-medium text-slate-900 dark:text-slate-100">{title}</h3>
      {children && <p className="mt-1 max-w-md text-sm text-slate-500">{children}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

// Shows an ApiError (message plus any detail lines). Used for failed loads and failed saves.
export function ErrorMessage({ error, onRetry, title = "Something went wrong" }) {
  if (!error) return null;
  return (
    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
      <div className="flex items-start gap-2">
        <Icon name="alert" className="mt-0.5 h-4 w-4 shrink-0" />
        <div className="min-w-0 flex-1">
          <p className="font-medium">{title}</p>
          <p className="mt-1">{error.message}</p>
          {error.errors?.length > 0 && (
            <ul className="mt-2 list-disc space-y-0.5 pl-5">
              {error.errors.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          )}
          {onRetry && (
            <button type="button" onClick={onRetry} className="mt-3 font-medium underline">
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function Notice({ tone = "info", icon, title, children }) {
  const tones = {
    info: "border-indigo-200 bg-indigo-50 text-indigo-900 dark:border-indigo-900 dark:bg-indigo-950/40 dark:text-indigo-200",
    warning: "border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200",
    danger: "border-red-200 bg-red-50 text-red-900 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200",
    success: "border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200",
  };
  return (
    <div className={`flex items-start gap-2 rounded-lg border p-3 text-sm ${tones[tone]}`}>
      <Icon name={icon || (tone === "info" ? "info" : "alert")} className="mt-0.5 h-4 w-4 shrink-0" />
      <div>
        {title && <p className="font-medium">{title}</p>}
        <div>{children}</div>
      </div>
    </div>
  );
}

// ---------- Status badges: always an icon plus text, never colour alone ----------

const TONES = {
  green: "bg-emerald-50 text-emerald-800 ring-emerald-600/20 dark:bg-emerald-950/50 dark:text-emerald-300 dark:ring-emerald-400/30",
  red: "bg-red-50 text-red-800 ring-red-600/20 dark:bg-red-950/50 dark:text-red-300 dark:ring-red-400/30",
  amber: "bg-amber-50 text-amber-800 ring-amber-600/20 dark:bg-amber-950/50 dark:text-amber-300 dark:ring-amber-400/30",
  indigo: "bg-indigo-50 text-indigo-800 ring-indigo-600/20 dark:bg-indigo-950/50 dark:text-indigo-300 dark:ring-indigo-400/30",
  slate: "bg-slate-100 text-slate-700 ring-slate-500/20 dark:bg-slate-800 dark:text-slate-300 dark:ring-slate-400/20",
};

export function Badge({ tone = "slate", icon, children, className = "" }) {
  return (
    <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${TONES[tone]} ${className}`}>
      {icon && <Icon name={icon} className="h-3.5 w-3.5" />}
      {children}
    </span>
  );
}

export function PassFailBadge({ passed, large = false }) {
  const size = large ? "px-3 py-1 text-sm" : "";
  return passed ? (
    <Badge tone="green" icon="check-circle" className={size}>Pass</Badge>
  ) : (
    <Badge tone="red" icon="x-circle" className={size}>Fail</Badge>
  );
}

const RULE_STATUS = {
  met: { tone: "green", icon: "check-circle", label: "Met" },
  partially_met: { tone: "amber", icon: "half-circle", label: "Partially met" },
  not_met: { tone: "red", icon: "x-circle", label: "Not met" },
};

export function RuleStatusBadge({ status }) {
  const s = RULE_STATUS[status] || { tone: "slate", icon: "info", label: status };
  return <Badge tone={s.tone} icon={s.icon}>{s.label}</Badge>;
}

const DOCUMENT_STATUS = {
  Passed: { tone: "green", icon: "check-circle" },
  Failed: { tone: "red", icon: "x-circle" },
  Corrected: { tone: "indigo", icon: "refresh" },
  "In review": { tone: "slate", icon: "clock" },
  Error: { tone: "amber", icon: "alert" },
};

export function DocumentStatusBadge({ status }) {
  const s = DOCUMENT_STATUS[status] || { tone: "slate", icon: "info" };
  return <Badge tone={s.tone} icon={s.icon}>{status}</Badge>;
}

export function WeightBadge({ weight }) {
  const tone = { high: "indigo", medium: "slate", low: "slate" }[weight];
  return <Badge tone={tone}>{weight[0].toUpperCase() + weight.slice(1)} weight</Badge>;
}

export function CriticalBadge() {
  return <Badge tone="red" icon="shield">Critical</Badge>;
}
