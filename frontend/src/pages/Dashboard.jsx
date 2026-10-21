// Dashboard. The charts and summary numbers come next (we'll write the SQL together first).
// For now: a short intro and the most recently updated documents.
import { Link } from "react-router-dom";
import { Button, Card, DocumentStatusBadge, EmptyState, ErrorMessage, Notice, PageHeader, Spinner } from "../components/ui";
import { useFetch } from "../lib/api";
import { formatDate } from "../lib/format";

export default function Dashboard() {
  const { data: documents, error, loading, reload } = useFetch("/api/documents?sort=updated&descending=true");
  const recent = (documents || []).slice(0, 10);

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Review volume, pass rates and the rules that fail most often." actions={<Button icon="plus" to="/new-review">New review</Button>} />
      <div className="mb-5">
        <Notice tone="info" title="Charts and summary numbers are the next step">
          The summary cards, charts and filters are being built next, after we agree the queries behind them.
        </Notice>
      </div>
      <Card title="Recent documents">
        {loading && <Spinner />}
        <ErrorMessage error={error} onRetry={reload} />
        {documents && recent.length === 0 && (
          <EmptyState icon="file" title="No reviews yet" action={<Button icon="plus" to="/new-review">Start your first review</Button>} />
        )}
        {recent.length > 0 && (
          <ul className="divide-y divide-slate-100 dark:divide-slate-800">
            {recent.map((d) => (
              <li key={d.id} className="flex flex-wrap items-center gap-3 py-3 text-sm">
                <Link to={`/documents/${d.id}`} className="min-w-0 flex-1 truncate font-medium hover:underline">{d.title}</Link>
                <span className="text-slate-500">{d.document_type_name}</span>
                <span className="w-10 text-right font-semibold">{d.latest_score ?? "—"}</span>
                <DocumentStatusBadge status={d.status} />
                <span className="w-24 text-right text-slate-500">{formatDate(d.updated_at)}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </>
  );
}
