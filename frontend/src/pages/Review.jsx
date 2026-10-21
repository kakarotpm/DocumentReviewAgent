// A review: shows progress while it runs, then the full results.
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Icon from "../components/Icon";
import RevisedUpload from "../components/RevisedUpload";
import ScoreGauge from "../components/ScoreGauge";
import SuggestionCard from "../components/SuggestionCard";
import {
  Badge, Button, Card, CriticalBadge, EmptyState, ErrorMessage, Notice, PageHeader, PassFailBadge, RuleStatusBadge, Spinner,
} from "../components/ui";
import { api, useFetch } from "../lib/api";
import { formatDateTime, formatPoints } from "../lib/format";

const POLL_MS = 2000;
const SUGGESTION_TABS = [
  { type: "add", label: "Missing (Add)" },
  { type: "change", label: "Change" },
  { type: "delete", label: "Delete" },
];
const STATUS_FILTERS = [
  { id: "all", label: "All" },
  { id: "not_met", label: "Not met" },
  { id: "partially_met", label: "Partially met" },
  { id: "met", label: "Met" },
];

export default function Review() {
  const { reviewId } = useParams();
  const { data: review, error, loading, reload } = useFetch(`/api/reviews/${reviewId}`);
  const running = review && (review.status === "queued" || review.status === "processing");

  // While the review runs, check again every 2 seconds.
  useEffect(() => {
    if (!running) return;
    const timer = setTimeout(reload, POLL_MS);
    return () => clearTimeout(timer);
  }, [running, review, reload]);

  if (loading && !review) return <Spinner label="Loading review…" />;
  if (error) {
    return error.status === 404 ? (
      <EmptyState icon="search" title="Review not found" action={<Button to="/documents">Go to Documents</Button>} />
    ) : (
      <ErrorMessage error={error} title="Couldn't load this review" onRetry={reload} />
    );
  }

  const header = (
    <PageHeader
      back={{ to: `/documents/${review.document_id}`, label: "Document" }}
      title={review.document_title}
      subtitle={
        <>
          {review.document_type_name} · Version {review.version_number}
          {review.project_name && <> · {review.project_name}</>} · {review.original_filename}
        </>
      }
    />
  );

  if (running) return <>{header}<Progress review={review} /></>;
  if (review.status === "error") return <>{header}<ReviewFailed review={review} /></>;
  return <>{header}<Results review={review} /></>;
}

function Progress({ review }) {
  const processing = review.status === "processing";
  const steps = [
    { label: "Reading document", state: "done" },
    { label: `Checking ${review.rule_count} rules`, state: processing ? "active" : "waiting" },
    { label: "Calculating score", state: "waiting" },
  ];
  return (
    <Card>
      <ol className="space-y-4">
        {steps.map((step) => (
          <li key={step.label} className="flex items-center gap-3 text-sm">
            {step.state === "done" && <Icon name="check-circle" className="h-5 w-5 text-emerald-600" />}
            {step.state === "active" && <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600" />}
            {step.state === "waiting" && <span className="h-5 w-5 rounded-full border-2 border-slate-300 dark:border-slate-600" />}
            <span className={step.state === "waiting" ? "text-slate-500" : "font-medium"}>{step.label}</span>
          </li>
        ))}
      </ol>
      <p className="mt-6 text-sm text-slate-500">
        This usually takes under two minutes. You can leave this page: the review keeps going and will appear in{" "}
        <Link to="/documents" className="font-medium text-indigo-700 hover:underline dark:text-indigo-400">Documents</Link>.
      </p>
    </Card>
  );
}

function ReviewFailed({ review }) {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const rerun = async () => {
    setBusy(true);
    try {
      const fresh = await api.post(`/api/reviews/${review.id}/rerun`);
      navigate(`/reviews/${fresh.id}`);
    } catch (e) {
      setError(e);
      setBusy(false);
    }
  };

  return (
    <Card>
      <ErrorMessage error={{ message: review.error_message }} title="This review didn't finish" />
      {error && <div className="mt-3"><ErrorMessage error={error} /></div>}
      <div className="mt-4 flex gap-2">
        <Button icon="refresh" onClick={rerun} disabled={busy}>{busy ? "Starting…" : "Re-run review"}</Button>
        <Button variant="secondary" to="/documents">Back to Documents</Button>
      </div>
    </Card>
  );
}

function Results({ review }) {
  const navigate = useNavigate();
  const [suggestionTab, setSuggestionTab] = useState("add");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showUpload, setShowUpload] = useState(false);
  const [rerunError, setRerunError] = useState(null);

  const suggestions = review.rules.flatMap((rule) => rule.suggestions.map((s) => ({ suggestion: s, rule })));
  const counts = Object.fromEntries(SUGGESTION_TABS.map((t) => [t.type, suggestions.filter((s) => s.suggestion.type === t.type).length]));
  const visibleRules = statusFilter === "all" ? review.rules : review.rules.filter((r) => r.status === statusFilter);
  const isLatest = review.version_number === review.latest_version_number;
  const c = review.comparison;

  const rerun = async () => {
    try {
      const fresh = await api.post(`/api/reviews/${review.id}/rerun`);
      navigate(`/reviews/${fresh.id}`);
    } catch (e) {
      setRerunError(e);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-2">
        {isLatest && <Button icon="upload" onClick={() => setShowUpload((v) => !v)}>Upload revised version</Button>}
        <Button variant="secondary" icon="refresh" onClick={rerun}>Re-run review</Button>
        <Button variant="secondary" icon="folder" to="/documents">Back to Documents</Button>
      </div>
      <ErrorMessage error={rerunError} title="Couldn't start a new review" />
      {showUpload && <RevisedUpload documentId={review.document_id} nextVersion={review.latest_version_number + 1} onCancel={() => setShowUpload(false)} />}
      {!isLatest && (
        <Notice tone="info">
          This is version {review.version_number}. A newer version exists:{" "}
          <Link to={`/documents/${review.document_id}`} className="font-medium underline">see all versions</Link>.
        </Notice>
      )}
      {review.is_demo && (
        <Notice tone="warning" title="Demo review">
          These results come from simple keyword matching, not AI, because no API key is set. Use them to try out the app,
          not to judge the document. Once a key is added, click Re-run review.
        </Notice>
      )}

      <div className="grid gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <div className="flex flex-col items-center text-center">
            <ScoreGauge score={review.score} threshold={review.pass_threshold} passed={review.passed} />
            <div className="mt-2"><PassFailBadge passed={review.passed} large /></div>
            <p className="mt-2 text-xs text-slate-500">Pass mark {review.pass_threshold}, and every critical rule must be at least partly met.</p>
            {c && (
              <div className="mt-4 w-full rounded-lg bg-slate-50 p-3 text-sm dark:bg-slate-800/50">
                <p className="flex items-center justify-center gap-1 font-medium">
                  <Icon name={c.score_change >= 0 ? "arrow-up" : "arrow-down"} className={`h-4 w-4 ${c.score_change >= 0 ? "text-emerald-600" : "text-red-600"}`} />
                  {c.score_change >= 0 ? "+" : ""}{c.score_change} from v{c.previous_version_number} (score {c.previous_score})
                </p>
                {c.rules_updated && <p className="mt-1 text-xs text-amber-700 dark:text-amber-400">The rulebook changed since v{c.previous_version_number}, so part of this change may come from the rules.</p>}
              </div>
            )}
          </div>
        </Card>

        <div className="space-y-5 lg:col-span-2">
          {review.critical_failures.length > 0 && (
            <Notice tone="danger" icon="shield" title="Critical rule failed">
              This document fails regardless of its score, because{" "}
              {review.critical_failures.map((r, i) => (
                <span key={r.rule_id}>{i > 0 && " and "}<strong>{r.rule_id} {r.title}</strong></span>
              ))}{" "}
              {review.critical_failures.length > 1 ? "are" : "is"} not met.
            </Notice>
          )}
          {c && (c.newly_met.length > 0 || c.newly_not_met.length > 0) && (
            <Card title={`Since version ${c.previous_version_number}`}>
              <div className="grid gap-4 text-sm sm:grid-cols-2">
                <div>
                  <p className="mb-1 font-medium text-emerald-700 dark:text-emerald-400">Now met ({c.newly_met.length})</p>
                  <ul className="space-y-0.5">{c.newly_met.map((r) => <li key={r.rule_id}>{r.rule_id} {r.title}</li>)}</ul>
                </div>
                <div>
                  <p className="mb-1 font-medium text-red-700 dark:text-red-400">Now not met ({c.newly_not_met.length})</p>
                  <ul className="space-y-0.5">{c.newly_not_met.map((r) => <li key={r.rule_id}>{r.rule_id} {r.title}</li>)}</ul>
                </div>
              </div>
            </Card>
          )}
          <Card title="Score by category">
            <ul className="space-y-3">
              {review.categories.map((cat) => {
                const pct = cat.points_possible ? (cat.points_earned / cat.points_possible) * 100 : 0;
                return (
                  <li key={cat.category}>
                    <div className="mb-1 flex justify-between text-sm">
                      <span>{cat.category}</span>
                      <span className="text-slate-500">{formatPoints(cat.points_earned)} / {cat.points_possible} pts</span>
                    </div>
                    <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-800">
                      <div className="h-2 rounded-full bg-indigo-500" style={{ width: `${pct}%` }} />
                    </div>
                  </li>
                );
              })}
            </ul>
          </Card>
        </div>
      </div>

      <Card title="Suggestions">
        <div className="mb-4 flex gap-1 border-b border-slate-200 dark:border-slate-800" role="tablist">
          {SUGGESTION_TABS.map((t) => (
            <button
              key={t.type}
              role="tab"
              aria-selected={suggestionTab === t.type}
              onClick={() => setSuggestionTab(t.type)}
              className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium ${
                suggestionTab === t.type ? "border-indigo-600 text-indigo-700 dark:text-indigo-300" : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
              }`}
            >
              {t.label} <Badge className="ml-1">{counts[t.type]}</Badge>
            </button>
          ))}
        </div>
        {counts[suggestionTab] === 0 ? (
          <p className="py-6 text-center text-sm text-slate-500">No suggestions of this kind.</p>
        ) : (
          <div className="space-y-3">
            {suggestions
              .filter((s) => s.suggestion.type === suggestionTab)
              .map(({ suggestion, rule }) => <SuggestionCard key={suggestion.id} suggestion={suggestion} rule={rule} />)}
          </div>
        )}
      </Card>

      <Card
        title="Rule checklist"
        actions={
          <div className="flex flex-wrap gap-1">
            {STATUS_FILTERS.map((f) => (
              <button
                key={f.id}
                type="button"
                onClick={() => setStatusFilter(f.id)}
                aria-pressed={statusFilter === f.id}
                className={`rounded-full px-3 py-1 text-xs font-medium ${
                  statusFilter === f.id ? "bg-slate-800 text-white dark:bg-slate-200 dark:text-slate-900" : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500 dark:border-slate-800">
              <tr>
                <th className="py-2 pr-3 font-medium">Rule</th>
                <th className="py-2 pr-3 font-medium">Status</th>
                <th className="py-2 pr-3 font-medium">Points</th>
                <th className="py-2 font-medium">Evidence and explanation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {visibleRules.map((r) => (
                <tr key={r.rule_id} className="align-top">
                  <td className="py-3 pr-3">
                    <span className="font-mono text-xs text-slate-500">{r.rule_id}</span>
                    <p className="font-medium">{r.title}</p>
                    <p className="mt-1 flex flex-wrap gap-1 text-xs text-slate-500">
                      {r.category} {r.critical && <CriticalBadge />}
                    </p>
                  </td>
                  <td className="py-3 pr-3"><RuleStatusBadge status={r.status} /></td>
                  <td className="whitespace-nowrap py-3 pr-3">{formatPoints(r.points_earned)} / {r.points_possible}</td>
                  <td className="py-3">
                    <p className="italic text-slate-700 dark:text-slate-300">"{r.evidence}"</p>
                    <p className="text-xs text-slate-500">{r.location}</p>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">{r.explanation}</p>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {visibleRules.length === 0 && <p className="py-6 text-center text-sm text-slate-500">No rules with this status.</p>}
        </div>
      </Card>

      <p className="text-xs text-slate-500">
        Reviewed {formatDateTime(review.completed_at)} · rulebook version {review.rulebook_version} · {review.model_name} · prompt {review.prompt_version}
      </p>
    </div>
  );
}
