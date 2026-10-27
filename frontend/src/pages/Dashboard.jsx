// Dashboard: summary numbers, four charts, filters and recent reviews. The SQL is in backend/app/services/dashboard.sql.
import { useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { Badge, Button, Card, EmptyState, ErrorMessage, PageHeader, PassFailBadge, Spinner } from "../components/ui";
import { useFetch } from "../lib/api";
import { axisProps, ChartState, ChartTooltip, DataTable, StatCard } from "../components/charts";
import { useChartColors } from "../lib/chartColors";
import { formatDate, formatDateTime } from "../lib/format";

const EMPTY_FILTERS = { from: "", to: "", type: "", project: "" };

export default function Dashboard() {
  const colors = useChartColors();
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [selectedRule, setSelectedRule] = useState(null);
  const types = useFetch("/api/document-types");
  const projects = useFetch("/api/documents/projects");

  const qs = new URLSearchParams(Object.fromEntries(Object.entries(filters).filter(([, v]) => v))).toString();
  const summary = useFetch(`/api/dashboard/summary?${qs}`);
  const byType = useFetch(`/api/dashboard/pass-fail-by-type?${qs}`);
  const trends = useFetch(`/api/dashboard/trends?${qs}`);
  const distribution = useFetch(`/api/dashboard/score-distribution?${qs}`);
  const topRules = useFetch(`/api/dashboard/top-failed-rules?${qs}`);
  const recent = useFetch(`/api/dashboard/recent-reviews?${qs}`);
  const affected = useFetch(selectedRule ? `/api/dashboard/top-failed-rules/${selectedRule.rule_id}/documents?${qs}` : null);

  const setFilter = (field, value) => {
    setFilters((f) => ({ ...f, [field]: value }));
    setSelectedRule(null);
  };
  const s = summary.data;
  const noData = s && s.documents === 0 && s.reviews_completed === 0;
  const filtered = Object.values(filters).some(Boolean);
  const weekLabel = (iso) => `Week of ${formatDate(iso)}`;
  const totalBuckets = (distribution.data || []).reduce((n, b) => n + b.reviews, 0);

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Review volume, pass rates, corrections and the rules that fail most often." actions={<Button icon="plus" to="/new-review">New review</Button>} />

      {/* Filters: one row above everything they affect. */}
      <div className="mb-5 flex flex-wrap items-end gap-2">
        <label className="text-xs text-slate-500">
          From
          <input type="date" className="input mt-1 w-40" value={filters.from} onChange={(e) => setFilter("from", e.target.value)} />
        </label>
        <label className="text-xs text-slate-500">
          To
          <input type="date" className="input mt-1 w-40" value={filters.to} onChange={(e) => setFilter("to", e.target.value)} />
        </label>
        <label className="text-xs text-slate-500">
          Document type
          <select className="input mt-1 w-56" value={filters.type} onChange={(e) => setFilter("type", e.target.value)}>
            <option value="">All types</option>
            {(types.data || []).map((t) => <option key={t.key} value={t.key}>{t.display_name}</option>)}
          </select>
        </label>
        <label className="text-xs text-slate-500">
          Project
          <select className="input mt-1 w-48" value={filters.project} onChange={(e) => setFilter("project", e.target.value)}>
            <option value="">All projects</option>
            {(projects.data || []).map((p) => <option key={p}>{p}</option>)}
          </select>
        </label>
        {filtered && <Button variant="ghost" onClick={() => { setFilters(EMPTY_FILTERS); setSelectedRule(null); }}>Clear filters</Button>}
      </div>

      <ErrorMessage error={summary.error} title="Couldn't load the dashboard" onRetry={summary.reload} />
      {summary.loading && !s && <Spinner />}

      {noData && !filtered && (
        <EmptyState icon="dashboard" title="No reviews yet" action={<Button icon="plus" to="/new-review">Start your first review</Button>}>
          Once documents are reviewed, their scores, pass rates and most common gaps appear here.
        </EmptyState>
      )}

      {s && !(noData && !filtered) && (
        <div className="space-y-5">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-7">
            <StatCard label="Documents" value={s.documents} hint="uploaded" />
            <StatCard label="Reviews" value={s.reviews_completed} hint="completed" />
            <StatCard label="Passed" value={s.passed} hint="documents" />
            <StatCard label="Failed" value={s.failed} hint="documents" />
            <StatCard label="Corrected" value={s.corrected} hint="failed, then passed" />
            <StatCard label="Pass rate" value={s.pass_rate == null ? null : `${s.pass_rate}%`} hint="of reviews" />
            <StatCard label="Average score" value={s.average_score} hint="of reviews" />
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <Card title="Pass vs fail by document type">
              <ChartState query={byType} empty={byType.data?.length === 0}>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={byType.data} barGap={2} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                    <CartesianGrid vertical={false} stroke={colors.grid} />
                    <XAxis dataKey="document_type" {...axisProps(colors)} interval={0} tickFormatter={(v) => (v.length > 18 ? v.slice(0, 17) + "…" : v)} />
                    <YAxis allowDecimals={false} {...axisProps(colors)} />
                    <Tooltip content={<ChartTooltip />} cursor={{ fill: colors.grid, opacity: 0.5 }} />
                    <Legend wrapperStyle={{ fontSize: 12, color: colors.text }} />
                    <Bar dataKey="passed" name="Passed" fill={colors.passed} radius={[4, 4, 0, 0]} maxBarSize={28} />
                    <Bar dataKey="failed" name="Failed" fill={colors.failed} radius={[4, 4, 0, 0]} maxBarSize={28} />
                  </BarChart>
                </ResponsiveContainer>
                <DataTable rows={byType.data || []} columns={[{ key: "document_type", label: "Type" }, { key: "passed", label: "Passed" }, { key: "failed", label: "Failed" }]} />
              </ChartState>
            </Card>

            <Card title="Score distribution">
              <ChartState query={distribution} empty={totalBuckets === 0}>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={distribution.data} barCategoryGap={2} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                    <CartesianGrid vertical={false} stroke={colors.grid} />
                    <XAxis dataKey="range" {...axisProps(colors)} interval={0} tick={{ fill: colors.axis, fontSize: 11 }} />
                    <YAxis allowDecimals={false} {...axisProps(colors)} />
                    <Tooltip content={<ChartTooltip labelFormatter={(r) => `Score ${r}`} />} cursor={{ fill: colors.grid, opacity: 0.5 }} />
                    <ReferenceLine x="80–89" stroke={colors.text} strokeDasharray="4 3" label={{ value: "Pass mark 80", position: "insideTopLeft", fill: colors.text, fontSize: 11 }} />
                    <Bar dataKey="reviews" name="Reviews" fill={colors.series} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
                <DataTable rows={distribution.data || []} columns={[{ key: "range", label: "Score" }, { key: "reviews", label: "Reviews" }]} />
              </ChartState>
            </Card>
          </div>

          <Card title="Reviews over time">
            <ChartState query={trends} empty={trends.data?.length === 0}>
              <p className="mb-2 text-xs font-medium text-slate-500">Reviews completed per week</p>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={trends.data} syncId="trends" margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
                  <CartesianGrid vertical={false} stroke={colors.grid} />
                  <XAxis dataKey="week_start" {...axisProps(colors)} tickFormatter={formatDate} />
                  <YAxis allowDecimals={false} {...axisProps(colors)} />
                  <Tooltip content={<ChartTooltip labelFormatter={weekLabel} />} cursor={{ fill: colors.grid, opacity: 0.5 }} />
                  <Bar dataKey="reviews" name="Reviews" fill={colors.series} radius={[4, 4, 0, 0]} maxBarSize={40} />
                </BarChart>
              </ResponsiveContainer>
              <p className="mb-2 mt-4 text-xs font-medium text-slate-500">Pass rate per week</p>
              <ResponsiveContainer width="100%" height={160}>
                <LineChart data={trends.data} syncId="trends" margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
                  <CartesianGrid vertical={false} stroke={colors.grid} />
                  <XAxis dataKey="week_start" {...axisProps(colors)} tickFormatter={formatDate} />
                  <YAxis domain={[0, 100]} unit="%" {...axisProps(colors)} />
                  <Tooltip content={<ChartTooltip labelFormatter={weekLabel} unit="%" />} cursor={{ stroke: colors.axis }} />
                  <Line dataKey="pass_rate" name="Pass rate" stroke={colors.series} strokeWidth={2} dot={{ r: 4, fill: colors.series, stroke: colors.surface, strokeWidth: 2 }} activeDot={{ r: 5 }} connectNulls />
                </LineChart>
              </ResponsiveContainer>
              <DataTable
                rows={(trends.data || []).map((w) => ({ ...w, week: weekLabel(w.week_start), rate: w.pass_rate == null ? null : `${w.pass_rate}%` }))}
                columns={[{ key: "week", label: "Week" }, { key: "reviews", label: "Reviews" }, { key: "rate", label: "Pass rate" }]}
              />
            </ChartState>
          </Card>

          <Card title="Most frequently failed rules (Not Met)">
            <ChartState query={topRules} empty={topRules.data?.length === 0}>
              <p className="mb-2 text-xs text-slate-500">Click a bar to see the documents that failed it.</p>
              <ResponsiveContainer width="100%" height={Math.max(120, (topRules.data?.length || 0) * 36)}>
                <BarChart data={topRules.data} layout="vertical" margin={{ top: 0, right: 24, left: 8, bottom: 0 }}>
                  <CartesianGrid horizontal={false} stroke={colors.grid} />
                  <XAxis type="number" allowDecimals={false} {...axisProps(colors)} />
                  <YAxis
                    type="category"
                    dataKey="rule_id"
                    width={210}
                    {...axisProps(colors)}
                    tickFormatter={(id) => {
                      const rule = topRules.data.find((r) => r.rule_id === id);
                      const label = `${id} ${rule?.rule_title || ""}`;
                      return label.length > 30 ? label.slice(0, 29) + "…" : label;
                    }}
                  />
                  <Tooltip
                    content={<ChartTooltip labelFormatter={(id) => { const r = topRules.data.find((x) => x.rule_id === id); return `${id} ${r?.rule_title} (${r?.document_type})`; }} />}
                    cursor={{ fill: colors.grid, opacity: 0.5 }}
                  />
                  <Bar
                    dataKey="times_not_met"
                    name="Times not met"
                    fill={colors.series}
                    radius={[0, 4, 4, 0]}
                    maxBarSize={22}
                    cursor="pointer"
                    onClick={(bar) => setSelectedRule(bar.payload ?? bar)}
                  />
                </BarChart>
              </ResponsiveContainer>
              <DataTable
                rows={topRules.data || []}
                columns={[{ key: "rule_id", label: "Rule" }, { key: "rule_title", label: "Title" }, { key: "document_type", label: "Type" }, { key: "times_not_met", label: "Times not met" }]}
              />
              {selectedRule && (
                <div className="mt-4 rounded-lg border border-slate-200 p-4 dark:border-slate-800">
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <p className="text-sm font-medium">Reviews where {selectedRule.rule_id} {selectedRule.rule_title} was not met</p>
                    <Button variant="ghost" onClick={() => setSelectedRule(null)}>Close</Button>
                  </div>
                  {affected.loading && <Spinner />}
                  <ErrorMessage error={affected.error} onRetry={affected.reload} />
                  {affected.data && (
                    <ul className="divide-y divide-slate-100 text-sm dark:divide-slate-800">
                      {affected.data.map((d) => (
                        <li key={d.review_id} className="flex flex-wrap items-center gap-3 py-2">
                          <Link to={`/reviews/${d.review_id}`} className="min-w-0 flex-1 truncate font-medium hover:underline">{d.title}</Link>
                          <span className="text-slate-500">v{d.version_number}</span>
                          {d.project_name && <span className="text-slate-500">{d.project_name}</span>}
                          <span className="w-8 text-right font-semibold">{d.score}</span>
                          <span className="w-28 text-right text-slate-500">{formatDate(d.completed_at)}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </ChartState>
          </Card>

          <Card title="Recent reviews">
            <ChartState query={recent} empty={recent.data?.length === 0}>
              <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                {(recent.data || []).map((r) => (
                  <li key={r.review_id} className="flex flex-wrap items-center gap-3 py-3 text-sm">
                    <Link to={`/reviews/${r.review_id}`} className="min-w-0 flex-1 truncate font-medium hover:underline">{r.title}</Link>
                    <span className="text-slate-500">{r.document_type} · v{r.version_number}</span>
                    <span className="w-8 text-right font-semibold">{r.score ?? "—"}</span>
                    {r.status === "complete" ? <PassFailBadge passed={Boolean(r.passed)} /> : <Badge icon={r.status === "error" ? "alert" : "clock"}>{r.status === "error" ? "Error" : "In review"}</Badge>}
                    <span className="w-36 text-right text-slate-500">{formatDateTime(r.created_at)}</span>
                  </li>
                ))}
              </ul>
            </ChartState>
          </Card>
        </div>
      )}
    </>
  );
}
