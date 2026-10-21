// Create a new document type: by hand, from a .md file, or from a description (AI).
// Opened from Rulebooks, or from New Review's "Custom type" card (?from=review).
import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import ChangePreview from "../components/ChangePreview";
import RuleEditor from "../components/RuleEditor";
import { MarkdownUpload, PromptRules } from "../components/RulebookSources";
import { PageHeader } from "../components/ui";
import { api } from "../lib/api";

const BLANK = { doc_type: "", display_name: "", description: "", pass_threshold: 80, rules: [] };
const METHODS = [
  { id: "manual", label: "Add rules by hand", icon: "pencil" },
  { id: "upload", label: "Upload a .md file", icon: "upload" },
  { id: "prompt", label: "Describe it (AI)", icon: "sparkles" },
];

export default function NewRulebook() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const fromReview = params.get("from") === "review";
  const [method, setMethod] = useState("manual");
  const [preview, setPreview] = useState(null);
  const [editStart, setEditStart] = useState(BLANK);
  const [editorKey, setEditorKey] = useState(0); // forces the editor to restart from editStart
  const [listed, setListed] = useState(true);
  const [existingKey, setExistingKey] = useState(null); // set when an uploaded .md turned out to be for an existing type
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const finish = (key) => navigate(fromReview ? `/new-review?type=${key}` : `/rulebooks/${key}`);

  const save = async ({ rulebook, changed_by, change_note, listed: listedFromPreview }) => {
    setSaving(true);
    setError(null);
    try {
      // An uploaded .md file can be for a type that already exists: then it's an update.
      const updateKey = preview?.mode === "update" ? rulebook.doc_type : existingKey;
      const saved = updateKey
          ? await api.put(`/api/document-types/${updateKey}`, { rulebook, changed_by, change_note })
          : await api.post("/api/document-types", { rulebook, changed_by, change_note, listed: listedFromPreview ?? listed });
      finish(saved.key);
    } catch (e) {
      setError(e);
    } finally {
      setSaving(false);
    }
  };

  const editFrom = (rulebook) => {
    setExistingKey(preview?.mode === "update" ? rulebook.doc_type : null);
    setEditStart(rulebook);
    setEditorKey((k) => k + 1);
    setPreview(null);
    setMethod("manual");
    setError(null);
  };

  return (
    <>
      <PageHeader
        back={fromReview ? { to: "/new-review", label: "New Review" } : { to: "/rulebooks", label: "Rulebooks" }}
        title="New document type"
        subtitle="Define the rules a document of this type must meet. You can change them later at any time."
      />

      {!preview && (
        <div className="mb-5 flex flex-wrap gap-2" role="tablist">
          {METHODS.map((m) => (
            <button
              key={m.id}
              role="tab"
              aria-selected={method === m.id}
              onClick={() => { setMethod(m.id); setError(null); }}
              className={`rounded-full border px-4 py-1.5 text-sm font-medium ${
                method === m.id
                  ? "border-indigo-600 bg-indigo-600 text-white"
                  : "border-slate-300 bg-white text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      )}

      {preview ? (
        <ChangePreview
          preview={preview}
          onSave={save}
          onEdit={editFrom}
          onCancel={() => setPreview(null)}
          saving={saving}
          error={error}
          showListedOption={fromReview}
        />
      ) : (
        <>
          {method === "manual" && (
            <>
              {fromReview && (
                <label className="mb-4 flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={listed} onChange={(e) => setListed(e.target.checked)} className="h-4 w-4 accent-indigo-600" />
                  Save as a reusable type (show it in the type list for future reviews)
                </label>
              )}
              <RuleEditor key={editorKey} initial={editStart} isNew={!existingKey} onSave={save} saving={saving} error={error} saveLabel="Create document type" />
            </>
          )}
          {method === "upload" && <MarkdownUpload onPreview={setPreview} />}
          {method === "prompt" && <PromptRules onPreview={setPreview} />}
        </>
      )}
    </>
  );
}
