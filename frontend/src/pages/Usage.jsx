// Usage Analytics: how many tokens the AI used and what it cost, with a weekly/monthly trend and model prices.
// The SQL is in backend/app/services/usage.sql.
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { axisProps, ChartState, ChartTooltip, DataTable, StatCard } from "../components/charts";
import { Badge, Button, Card, EmptyState, ErrorMessage, Field, Notice, PageHeader, Spinner } from "../components/ui";
import { api, useFetch } from "../lib/api";
import { useChartColors } from "../lib/chartColors";
import { formatCost, formatDate, formatDateTime, formatTokens, rememberName, savedName } from "../lib/format";
import { useHealth } from "../lib/health";

const PURPOSE_LABELS = {
  document_review: "Document review",
  workbook_review: "Excel workbook review",
  draft_rules: "AI drafting a new type",
  draft_rule: "AI drafting a rule",
};
const MEASURES = {
  cost: { label: "Spend", name: "Spend (US$)", format: formatCost, axis: (v) => `$${v}` },
  tokens: { label: "Tokens", name: "Tokens", format: formatTokens, axis: formatTokens },
};

function isoDay(d) {
  return d.toISOString().slice(0, 10);
}

// Quick date ranges; each returns { from, to } as YYYY-MM-DD ("" = open-ended).
const RANGES = [
  { id: "30d", label: "Last 30 days", get: () => ({ from: isoDay(new Date(Date.now() - 29 * 86400000)), to: isoDay(new Date()) }) },
  { id: "12m", label: "Last 12 months", get: () => { const d = new Date(); d.setFullYear(d.getFullYear() - 1); return { from: isoDay(d), to: isoDay(new Date()) }; } },
  { id: "all", label: "All time", get: () => ({ from: "", to: "" }) },
];

function Toggle({ options, value, onChange, label }) {
  return (
    <div className="inline-flex rounded-md border border-slate-300 p-0.5 dark:border-slate-700" role="group" aria-label={label}>
      {options.map(([id, text]) => (
        <button
          key={id}
          type="button"
          aria-pressed={value === id}
          onClick={() => onChange(id)}
          className={`rounded px-3 py-1 text-xs font-medium ${
            value === id ? "bg-slate-800 text-white dark:bg-slate-200 dark:text-slate-900" : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
          }`}
        >
          {text}
        </button>
      ))}
    </div>
  );
}

export default function Usage() {
  const colors = useChartColors();
  const { aiAvailable } = useHealth();
  const [dates, setDates] = useState(RANGES[0].get());
  const [period, setPeriod] = useState("week");
  const [measure, setMeasure] = useState("cost");

  const qs = new URLSearchParams(Object.fromEntries(Object.entries(dates).filter(([, v]) => v))).toString();
  const summary = useFetch(`/api/usage/summary?${qs}`);
  const trend = useFetch(`/api/usage/trend?period=${period}&${qs}`);
  const byModel = useFetch(`/api/usage/by-model?${qs}`);
  const byPurpose = useFetch(`/api/usage/by-purpose?${qs}`);
  const prices = useFetch("/api/usage/prices");

  const reloadAll = () => [summary, trend, byModel, byPurpose, prices].forEach((q) => q.reload());
  const s = summary.data;
  const m = MEASURES[measure];
  const periodLabel = (iso) =>
    period === "week" ? `Week of ${formatDate(iso)}` : new Date(iso + "T00:00:00").toLocaleDateString(undefined, { month: "long", year: "numeric" });
  const tickLabel = (iso) =>
    period === "week" ? formatDate(iso) : new Date(iso + "T00:00:00").toLocaleDateString(undefined, { month: "short", year: "numeric" });
  const rangeId = RANGES.find((r) => { const v = r.get(); return v.from === dates.from && v.to === dates.to; })?.id;

  return (
    <>
      <PageHeader title="Usage Analytics" subtitle="How many tokens the AI used and what it cost: every review and every AI rule draft." />

      {/* Filters: one row above everything they affect. */}
      <div className="mb-5 flex flex-wrap items-end gap-2">
        <label className="text-xs text-slate-500">
          From
          <input type="date" className="input mt-1 w-40" value={dates.from} onChange={(e) => setDates((d) => ({ ...d, from: e.target.value }))} />
        </label>
        <label className="text-xs text-slate-500">
          To
          <input type="date" className="input mt-1 w-40" value={dates.to} onChange={(e) => setDates((d) => ({ ...d, to: e.target.value }))} />
        </label>
        <Toggle label="Quick date range" options={RANGES.map((r) => [r.id, r.label])} value={rangeId} onChange={(id) => setDates(RANGES.find((r) => r.id === id).get())} />
      </div>

      {!aiAvailable && (
        <div className="mb-5">
          <Notice tone="info" title="Demo mode">
            No AI key is set, so reviews use keyword matching and no tokens are used. Nothing new is counted until a key is added.
          </Notice>
        </div>
      )}

      <ErrorMessage error={summary.error} title="Couldn't load usage" onRetry={summary.reload} />
      {summary.loading && !s && <Spinner />}

      {s && s.calls === 0 && !dates.from && !dates.to ? (
        <EmptyState icon="dashboard" title="No AI usage yet">
          Usage is recorded for every AI review and AI rule draft from now on. Demo reviews don't use the AI, so they aren't counted.
        </EmptyState>
      ) : s && (
        <div className="space-y-5">
          {s.unpriced_calls > 0 && (
            <Notice tone="warning" title="Some costs are missing">
              {s.unpriced_calls} AI call{s.unpriced_calls > 1 ? "s use a model" : " uses a model"} with no price set, so the spend shown is
              lower than the real cost. Add the price under Model prices below; it applies to those calls straight away.
            </Notice>
          )}

          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatCard label="Spend" value={formatCost(s.cost ?? 0)} hint="US dollars, at the prices below" />
            <StatCard label="Tokens" value={formatTokens(s.total_tokens)} hint={`${formatTokens(s.input_tokens)} in · ${formatTokens(s.output_tokens)} out`} />
            <StatCard label="AI calls" value={s.calls.toLocaleString()} hint={`${s.reviews} review${s.reviews === 1 ? "" : "s"}`} />
            <StatCard label="Cost per review" value={formatCost(s.cost_per_review)} hint="Average, including retries" />
          </div>

          <Card
            title={`${m.label} per ${period}`}
            actions={
              <div className="flex flex-wrap gap-2">
                <Toggle label="Measure" options={[["cost", "Spend"], ["tokens", "Tokens"]]} value={measure} onChange={setMeasure} />
                <Toggle label="Period" options={[["week", "Week"], ["month", "Month"]]} value={period} onChange={setPeriod} />
              </div>
            }
          >
            <ChartState query={trend} empty={trend.data?.length === 0} emptyText="No AI usage in this date range.">
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={trend.data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid vertical={false} stroke={colors.grid} />
                  <XAxis dataKey="period_start" {...axisProps(colors)} tickFormatter={tickLabel} />
                  <YAxis {...axisProps(colors)} tickFormatter={m.axis} width={56} />
                  <Tooltip content={<ChartTooltip labelFormatter={periodLabel} valueFormatter={m.format} />} cursor={{ fill: colors.grid, opacity: 0.5 }} />
                  <Bar dataKey={measure} name={m.name} fill={colors.series} radius={[4, 4, 0, 0]} maxBarSize={40} isAnimationActive={false} />
                </BarChart>
              </ResponsiveContainer>
              <DataTable
                rows={(trend.data || []).map((r) => ({ ...r, period: periodLabel(r.period_start), cost: formatCost(r.cost), tokens: formatTokens(r.tokens) }))}
                columns={[{ key: "period", label: period === "week" ? "Week" : "Month" }, { key: "cost", label: "Spend" }, { key: "tokens", label: "Tokens" }, { key: "calls", label: "AI calls" }]}
              />
            </ChartState>
          </Card>

          <div className="grid gap-5 lg:grid-cols-2">
            <Card title="By model">
              <ChartState query={byModel} empty={byModel.data?.length === 0} emptyText="No AI usage in this date range.">
                <BreakdownTable
                  rows={(byModel.data || []).map((r) => ({
                    key: r.model,
                    label: <>{r.model} <span className="text-xs text-slate-500">· {r.provider}</span>{!r.has_price && <Badge tone="amber" className="ml-1">No price</Badge>}</>,
                    calls: r.calls, tokens: r.input_tokens + r.output_tokens, cost: r.cost,
                  }))}
                />
              </ChartState>
            </Card>
            <Card title="By purpose">
              <ChartState query={byPurpose} empty={byPurpose.data?.length === 0} emptyText="No AI usage in this date range.">
                <BreakdownTable
                  rows={(byPurpose.data || []).map((r) => ({ key: r.purpose, label: PURPOSE_LABELS[r.purpose] || r.purpose, calls: r.calls, tokens: r.tokens, cost: r.cost }))}
                />
              </ChartState>
            </Card>
          </div>
        </div>
      )}

      <div className="mt-5">
        <Prices query={prices} onSaved={reloadAll} />
      </div>
    </>
  );
}

function BreakdownTable({ rows }) {
  const total = rows.reduce((n, r) => n + (r.cost || 0), 0);
  return (
    <table className="w-full text-left text-sm">
      <thead className="text-xs text-slate-500">
        <tr>
          <th className="py-1 pr-3 font-medium" />
          <th className="py-1 pr-3 text-right font-medium">AI calls</th>
          <th className="py-1 pr-3 text-right font-medium">Tokens</th>
          <th className="py-1 text-right font-medium">Spend</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.key} className="border-t border-slate-100 dark:border-slate-800">
            <td className="py-2 pr-3">{r.label}</td>
            <td className="py-2 pr-3 text-right tabular-nums">{r.calls.toLocaleString()}</td>
            <td className="py-2 pr-3 text-right tabular-nums">{formatTokens(r.tokens)}</td>
            <td className="py-2 text-right tabular-nums">
              {formatCost(r.cost)}
              {total > 0 && r.cost != null && <span className="ml-1 text-xs text-slate-500">({Math.round((r.cost / total) * 100)}%)</span>}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// ---------- Model prices ----------

const PRICE_FIELDS = [
  ["input_per_million", "Input"],
  ["cached_input_per_million", "Cached input"],
  ["output_per_million", "Output"],
];

function PriceRow({ price, name, onSaved, isNew = false }) {
  const [draft, setDraft] = useState(price);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  useEffect(() => setDraft(price), [price]);

  const changed = isNew || PRICE_FIELDS.some(([f]) => String(draft[f]) !== String(price[f]));
  const save = async () => {
    setBusy(true);
    setError(null);
    rememberName(name);
    try {
      await api.put("/api/usage/prices", {
        model: draft.model,
        ...Object.fromEntries(PRICE_FIELDS.map(([f]) => [f, Number(draft[f]) || 0])),
        updated_by: name,
      });
      onSaved();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <tr className="border-t border-slate-100 align-top dark:border-slate-800">
      <td className="py-2 pr-3">
        {isNew && !price.model ? (
          <input className="input py-1" aria-label="Model name" placeholder="model name" value={draft.model} onChange={(e) => setDraft({ ...draft, model: e.target.value })} />
        ) : (
          <span className="font-mono text-sm">{draft.model}</span>
        )}
        {price.updated_by && <p className="mt-0.5 text-xs text-slate-500">{price.updated_by}, {formatDateTime(price.updated_at)}</p>}
        {error && <p className="mt-1 text-xs text-red-700 dark:text-red-400" role="alert">{error.message}</p>}
      </td>
      {PRICE_FIELDS.map(([f, label]) => (
        <td key={f} className="py-2 pr-3">
          <div className="flex items-center gap-1">
            <span className="text-slate-500">$</span>
            <input
              type="number" min="0" step="0.01" className="input w-24 py-1 text-right" aria-label={`${label} price for ${draft.model || "new model"}`}
              value={draft[f]} onChange={(e) => setDraft({ ...draft, [f]: e.target.value })}
            />
          </div>
        </td>
      ))}
      <td className="py-2 text-right">
        <Button variant={changed ? "primary" : "secondary"} onClick={save} disabled={busy || !changed || !name.trim() || !draft.model.trim()}>
          {busy ? "Saving…" : "Save"}
        </Button>
      </td>
    </tr>
  );
}

function Prices({ query, onSaved }) {
  const [name, setName] = useState(savedName());
  const [adding, setAdding] = useState(false);
  const data = query.data;
  const blank = (model = "") => ({ model, input_per_million: "", cached_input_per_million: "", output_per_million: "" });
  const saved = () => { setAdding(false); onSaved(); };

  return (
    <Card title="Model prices" actions={<Button variant="secondary" icon="plus" onClick={() => setAdding(true)} disabled={adding}>Add a model</Button>}>
      <p className="mb-3 text-sm text-slate-600 dark:text-slate-400">
        US dollars per 1 million tokens. Copy them from your provider's pricing page (or your Azure agreement). A changed price
        applies to calls from now on; past spending keeps the price it had, except calls that had no price at all.
      </p>
      {query.loading && !data && <Spinner />}
      <ErrorMessage error={query.error} onRetry={query.reload} />
      {data && (
        <>
          <div className="mb-3 max-w-xs">
            <Field label="Your name" required hint="Recorded with each price change.">
              <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
            </Field>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="text-xs text-slate-500">
                <tr>
                  <th className="py-1 pr-3 font-medium">Model</th>
                  {PRICE_FIELDS.map(([f, label]) => <th key={f} className="py-1 pr-3 font-medium">{label}</th>)}
                  <th />
                </tr>
              </thead>
              <tbody>
                {data.prices.map((p) => (
                  <PriceRow key={p.model} price={p} name={name} onSaved={saved} />
                ))}
                {data.missing.map((model) => (
                  <PriceRow key={`missing-${model}`} price={blank(model)} name={name} onSaved={saved} isNew />
                ))}
                {adding && <PriceRow price={blank()} name={name} onSaved={saved} isNew />}
              </tbody>
            </table>
          </div>
          {data.missing.length > 0 && (
            <p className="mt-2 text-xs text-amber-700 dark:text-amber-400">
              No price yet for {data.missing.join(", ")}{data.missing.includes(data.current_model) && " (the model reviews use now)"}. Fill in the row and click Save.
            </p>
          )}
          {data.current_model && (
            <p className="mt-2 text-xs text-slate-500">Reviews currently use {data.current_provider}, model <span className="font-mono">{data.current_model}</span>.</p>
          )}
        </>
      )}
    </Card>
  );
}
