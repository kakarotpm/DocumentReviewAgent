// Start a review: choose a document type, upload the file, fill in the details, run.
import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import FileDropzone from "../components/FileDropzone";
import Icon from "../components/Icon";
import WorkbookUpload from "../components/WorkbookUpload";
import { Button, Card, ErrorMessage, Field, PageHeader, Spinner } from "../components/ui";
import { api, useFetch } from "../lib/api";
import { useHealth } from "../lib/health";
import { rememberName, savedName } from "../lib/format";

function StepTitle({ number, children }) {
  return (
    <span className="flex items-center gap-2">
      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-600 text-xs font-semibold text-white">{number}</span>
      {children}
    </span>
  );
}

export default function NewReview() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { aiAvailable, provider } = useHealth();
  const types = useFetch("/api/document-types");
  const projects = useFetch("/api/documents/projects");

  const [typeKey, setTypeKey] = useState(params.get("type") || "");
  const [file, setFile] = useState(null);
  const [wantWorkbook, setWantWorkbook] = useState(false);
  const [workbook, setWorkbook] = useState(null);
  const [title, setTitle] = useState("");
  const [titleEdited, setTitleEdited] = useState(false);
  const [project, setProject] = useState("");
  const [name, setName] = useState(savedName());
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Pre-fill the title from the file name until the user types their own.
  useEffect(() => {
    if (!titleEdited) setTitle(file ? file.name.replace(/\.[^.]+$/, "") : "");
  }, [file, titleEdited]);

  // The workbook option only appears for types whose rulebook has Excel rules (Part B).
  const hasExcelRules = Boolean(types.data?.find((t) => t.key === typeKey)?.has_excel_rules);
  const useWorkbook = hasExcelRules && wantWorkbook;
  const ready = typeKey && file && (!useWorkbook || workbook) && name.trim() && title.trim();

  const run = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    rememberName(name);
    const form = new FormData();
    form.append("file", file);
    form.append("document_type", typeKey);
    form.append("uploaded_by", name);
    form.append("title", title);
    form.append("project_name", project);
    if (useWorkbook) form.append("workbook", workbook);
    try {
      const result = await api.upload("/api/documents", form);
      navigate(`/reviews/${result.review_id}`);
    } catch (e) {
      setError(e);
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={run}>
      <PageHeader title="New review" subtitle="Check a document against its rulebook and get a score with specific suggestions." />
      <div className="space-y-5">
        <Card title={<StepTitle number={1}>Choose the document type</StepTitle>}>
          {types.loading && <Spinner />}
          <ErrorMessage error={types.error} title="Couldn't load document types" onRetry={types.reload} />
          {types.data && (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {types.data.map((t) => {
                const selected = typeKey === t.key;
                return (
                  <div
                    key={t.key}
                    className={`relative rounded-lg border p-4 transition ${
                      selected ? "border-indigo-600 ring-2 ring-indigo-600/20" : "border-slate-200 hover:border-indigo-300 dark:border-slate-700"
                    }`}
                  >
                    <button type="button" onClick={() => setTypeKey(t.key)} className="block w-full text-left" aria-pressed={selected}>
                      <span className="flex items-center justify-between gap-2">
                        <span className="font-medium text-slate-900 dark:text-slate-100">{t.display_name}</span>
                        {selected && <Icon name="check-circle" className="h-5 w-5 text-indigo-600" />}
                      </span>
                      <span className="mt-1 block text-sm text-slate-600 dark:text-slate-400">{t.description}</span>
                    </button>
                    <Link to={`/rulebooks/${t.key}`} className="mt-2 inline-block text-xs font-medium text-indigo-700 hover:underline dark:text-indigo-400">
                      View {t.rule_count} rules
                    </Link>
                  </div>
                );
              })}
              <Link
                to="/rulebooks/new?from=review"
                className="flex flex-col justify-center rounded-lg border border-dashed border-slate-300 p-4 text-left hover:border-indigo-400 dark:border-slate-700"
              >
                <span className="flex items-center gap-2 font-medium text-slate-900 dark:text-slate-100"><Icon name="plus" /> Custom type</span>
                <span className="mt-1 text-sm text-slate-600 dark:text-slate-400">Define rules for a document type that isn't listed.</span>
              </Link>
            </div>
          )}
          {types.data && typeKey && !types.data.some((t) => t.key === typeKey) && (
            <p className="mt-3 flex items-center gap-2 text-sm font-medium text-indigo-700 dark:text-indigo-400">
              <Icon name="check-circle" /> Using your one-off custom type "{typeKey}".
            </p>
          )}
        </Card>

        <Card title={<StepTitle number={2}>Upload the document</StepTitle>}>
          <FileDropzone file={file} onChange={setFile} />
          {hasExcelRules && (
            <WorkbookUpload wanted={wantWorkbook} onWantedChange={setWantWorkbook} file={workbook} onFileChange={setWorkbook} />
          )}
          <p className="mt-3 flex items-start gap-2 text-xs text-slate-500">
            <Icon name="shield" className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            {aiAvailable
              ? `The text of the document (and the workbook, if added) is sent to the AI service (${provider}) to be reviewed. The files themselves aren't stored; only their text is kept.`
              : "Demo mode: nothing is sent anywhere. The files themselves aren't stored; only their text is kept."}
          </p>
        </Card>

        <Card title={<StepTitle number={3}>Details</StepTitle>}>
          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="Document title" required>
              <input className="input" value={title} onChange={(e) => { setTitle(e.target.value); setTitleEdited(true); }} />
            </Field>
            <Field label="Project">
              <input className="input" list="projects" value={project} onChange={(e) => setProject(e.target.value)} placeholder="e.g. AP Automation" />
              <datalist id="projects">{(projects.data || []).map((p) => <option key={p} value={p} />)}</datalist>
            </Field>
            <Field label="Your name" required>
              <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
            </Field>
          </div>
        </Card>

        {error && <ErrorMessage error={error} title="The review couldn't start" />}
        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" icon="check" disabled={!ready || submitting}>
            {submitting ? "Uploading…" : "Run review"}
          </Button>
          {!ready && (
            <span className="text-sm text-slate-500">
              {!typeKey
                ? "Choose a document type"
                : !file
                  ? "Upload a file"
                  : useWorkbook && !workbook
                    ? "Add the Excel workbook (or untick the box)"
                    : "Fill in the title and your name"}{" "}
              to continue.
            </span>
          )}
        </div>
      </div>
    </form>
  );
}
