// The two "bring rules in" panels: upload a .md file, or describe changes in a prompt.
// Both ask the backend for a preview; nothing is saved here.
import { useState } from "react";
import { api } from "../lib/api";
import { useHealth } from "../lib/health";
import Icon from "./Icon";
import { Button, Card, ErrorMessage, Field, Notice } from "./ui";

export function MarkdownUpload({ targetKey, onPreview, onCancel }) {
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const submit = async () => {
    setBusy(true);
    setError(null);
    const form = new FormData();
    form.append("file", file);
    form.append("target_key", targetKey || "");
    try {
      onPreview(await api.upload("/api/document-types/import-preview", form));
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title="Upload a rulebook (.md)">
      <p className="mb-4 text-sm text-slate-600 dark:text-slate-400">
        Use the same format as a downloaded rulebook. Tip: download the current rulebook, edit it in any text editor, and
        upload it here. You'll see exactly what changes before anything is saved.
      </p>
      <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-dashed border-slate-300 p-4 text-sm hover:border-indigo-400 dark:border-slate-700">
        <Icon name="upload" className="h-5 w-5 text-slate-400" />
        <span>{file ? file.name : "Choose a .md file"}</span>
        <input type="file" accept=".md,text/markdown" className="sr-only" onChange={(e) => { setFile(e.target.files[0] || null); setError(null); }} />
      </label>
      {error && <div className="mt-4"><ErrorMessage error={error} title="This file can't be used yet" /></div>}
      <div className="mt-4 flex gap-2">
        <Button icon="search" onClick={submit} disabled={!file || busy}>{busy ? "Checking…" : "Preview changes"}</Button>
        {onCancel && <Button variant="secondary" onClick={onCancel}>Cancel</Button>}
      </div>
    </Card>
  );
}

export function PromptRules({ targetKey, onPreview, onCancel }) {
  const { aiAvailable } = useHealth();
  const [instruction, setInstruction] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const isNew = !targetKey;

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const body = { instruction, target_key: targetKey || null, display_name: isNew ? displayName : null };
      onPreview(await api.post("/api/document-types/prompt-preview", body));
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title={isNew ? "Describe the new document type" : "Describe the changes"}>
      {!aiAvailable && (
        <div className="mb-4">
          <Notice tone="warning" title="Needs the AI">
            Writing rules from a description needs an Anthropic API key, which isn't set yet. You can still add rules
            by hand or upload a .md file.
          </Notice>
        </div>
      )}
      <div className="space-y-4">
        {isNew && (
          <Field label="Name of the document type" required>
            <input className="input" value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder="e.g. Data Migration Plan" />
          </Field>
        )}
        <Field
          label={isNew ? "What must a good document of this type contain?" : "What should change?"}
          required
          hint={isNew ? "The AI drafts about 10 rules. You can edit them before saving." : "Only the changes you ask for are made, and you'll see them before saving."}
        >
          <textarea
            className="input min-h-32"
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder={
              isNew
                ? "e.g. A data migration plan must map every source field to a target field, define data quality checks, describe reconciliation, include a rollback plan, and name an owner for each step."
                : "e.g. Add a rule requiring a data retention section. Make the risks rule critical."
            }
          />
        </Field>
      </div>
      {error && <div className="mt-4"><ErrorMessage error={error} title="Couldn't draft the rules" /></div>}
      <div className="mt-4 flex gap-2">
        <Button icon="sparkles" onClick={submit} disabled={busy || !instruction.trim() || (isNew && !displayName.trim())}>
          {busy ? "Drafting… (this can take up to a minute)" : "Draft with AI"}
        </Button>
        {onCancel && <Button variant="secondary" onClick={onCancel}>Cancel</Button>}
      </div>
    </Card>
  );
}
