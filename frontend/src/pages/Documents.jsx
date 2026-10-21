// All documents: search, filter, sort; click a row for its versions.
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Icon from "../components/Icon";
import { Button, DocumentStatusBadge, EmptyState, ErrorMessage, PageHeader, Spinner } from "../components/ui";
import { useFetch } from "../lib/api";
import { formatDate } from "../lib/format";

const COLUMNS = [
  { id: "title", label: "Title" },
  { id: "type", label: "Type" },
  { id: "project", label: "Project" },
  { id: "uploaded_by", label: "Uploaded by" },
  { id: "score", label: "Latest score" },
  { id: "status", label: "Status" },
  { id: "versions", label: "Versions" },
  { id: "updated", label: "Last updated" },
];
const STATUSES = ["Passed", "Failed", "Corrected", "In review", "Error"];
const EMPTY_FILTERS = { search: "", document_type: "", status: "", project: "", date_from: "", date_to: "" };

export default function Documents() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [sort, setSort] = useState({ by: "updated", descending: true });
  const types = useFetch("/api/document-types");
  const projects = useFetch("/api/documents/projects");

  const query = new URLSearchParams({ ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v)), sort: sort.by, descending: sort.descending });
  const { data: documents, error, loading, reload } = useFetch(`/api/documents?${query}`);
  const filtered = Object.values(filters).some(Boolean);

  const setFilter = (field, value) => setFilters((f) => ({ ...f, [field]: value }));
  const sortBy = (by) => setSort((s) => ({ by, descending: s.by === by ? !s.descending : by === "updated" || by === "score" }));

  return (
    <>
      <PageHeader title="Documents" subtitle="Every uploaded document with its latest result." actions={<Button icon="plus" to="/new-review">New review</Button>} />

      <div className="mb-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-6">
        <div className="relative lg:col-span-2">
          <Icon name="search" className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input className="input pl-9" placeholder="Search by title" value={filters.search} onChange={(e) => setFilter("search", e.target.value)} aria-label="Search by title" />
        </div>
        <select className="input" value={filters.document_type} onChange={(e) => setFilter("document_type", e.target.value)} aria-label="Document type">
          <option value="">All types</option>
          {(types.data || []).map((t) => <option key={t.key} value={t.key}>{t.display_name}</option>)}
        </select>
        <select className="input" value={filters.status} onChange={(e) => setFilter("status", e.target.value)} aria-label="Status">
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s}>{s}</option>)}
        </select>
        <select className="input" value={filters.project} onChange={(e) => setFilter("project", e.target.value)} aria-label="Project">
          <option value="">All projects</option>
          {(projects.data || []).map((p) => <option key={p}>{p}</option>)}
        </select>
        <div className="flex gap-2">
          <input type="date" className="input" value={filters.date_from} onChange={(e) => setFilter("date_from", e.target.value)} aria-label="Updated from" title="Updated from" />
          <input type="date" className="input" value={filters.date_to} onChange={(e) => setFilter("date_to", e.target.value)} aria-label="Updated to" title="Updated to" />
        </div>
      </div>

      {loading && !documents && <Spinner />}
      <ErrorMessage error={error} title="Couldn't load documents" onRetry={reload} />
      {documents && documents.length === 0 && (
        filtered ? (
          <EmptyState icon="search" title="No documents match these filters" action={<Button variant="secondary" onClick={() => setFilters(EMPTY_FILTERS)}>Clear filters</Button>} />
        ) : (
          <EmptyState icon="file" title="No documents yet" action={<Button icon="plus" to="/new-review">Start your first review</Button>}>
            Upload a BRD, FRD, process document or roadmap to get a score and suggestions.
          </EmptyState>
        )
      )}
      {documents && documents.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          <table className="w-full min-w-[860px] text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:border-slate-800 dark:bg-slate-800/50">
              <tr>
                {COLUMNS.map((col) => (
                  <th key={col.id} className="px-4 py-3 font-medium" aria-sort={sort.by === col.id ? (sort.descending ? "descending" : "ascending") : "none"}>
                    <button type="button" onClick={() => sortBy(col.id)} className="inline-flex items-center gap-1 uppercase hover:text-slate-800 dark:hover:text-slate-200">
                      {col.label}
                      {sort.by === col.id && <Icon name={sort.descending ? "arrow-down" : "arrow-up"} className="h-3 w-3" />}
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {documents.map((d) => (
                <tr
                  key={d.id}
                  onClick={() => navigate(`/documents/${d.id}`)}
                  onKeyDown={(e) => e.key === "Enter" && navigate(`/documents/${d.id}`)}
                  tabIndex={0}
                  className="cursor-pointer hover:bg-slate-50 focus:bg-slate-50 focus:outline-none dark:hover:bg-slate-800/50 dark:focus:bg-slate-800/50"
                >
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{d.title}</td>
                  <td className="px-4 py-3">{d.document_type_name}</td>
                  <td className="px-4 py-3">{d.project_name || <span className="text-slate-400">—</span>}</td>
                  <td className="px-4 py-3">{d.uploaded_by}</td>
                  <td className="px-4 py-3">{d.latest_score ?? <span className="text-slate-400">—</span>}</td>
                  <td className="px-4 py-3"><DocumentStatusBadge status={d.status} /></td>
                  <td className="px-4 py-3">{d.versions}</td>
                  <td className="px-4 py-3 text-slate-500">{formatDate(d.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
