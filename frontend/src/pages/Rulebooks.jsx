// List of all document types and their rulebooks.
import { Link } from "react-router-dom";
import { Badge, Button, EmptyState, ErrorMessage, PageHeader, Spinner } from "../components/ui";
import { useFetch } from "../lib/api";

export default function Rulebooks() {
  const { data: types, error, loading, reload } = useFetch("/api/document-types");

  return (
    <>
      <PageHeader
        title="Rulebooks"
        subtitle="The rules each document type is reviewed against. Anyone can view and change them; every change is kept in the version history."
        actions={<Button icon="plus" to="/rulebooks/new">New document type</Button>}
      />
      {loading && <Spinner />}
      <ErrorMessage error={error} title="Couldn't load the rulebooks" onRetry={reload} />
      {types && types.length === 0 && (
        <EmptyState icon="book" title="No document types yet" action={<Button icon="plus" to="/rulebooks/new">New document type</Button>}>
          Create a document type to start reviewing documents.
        </EmptyState>
      )}
      {types && types.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {types.map((t) => (
            <Link
              key={t.key}
              to={`/rulebooks/${t.key}`}
              className="flex flex-col rounded-xl border border-slate-200 bg-white p-5 transition hover:border-indigo-300 hover:shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-700"
            >
              <div className="flex items-start justify-between gap-2">
                <h2 className="font-semibold text-slate-900 dark:text-slate-100">{t.display_name}</h2>
                <Badge tone={t.is_builtin ? "slate" : "indigo"}>{t.is_builtin ? "Built-in" : "Custom"}</Badge>
              </div>
              <p className="mt-2 flex-1 text-sm text-slate-600 dark:text-slate-400">{t.description}</p>
              <p className="mt-4 text-xs text-slate-500">
                {t.rule_count} rules{t.has_excel_rules && " (incl. Excel)"} · version {t.version}
              </p>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
