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

// A text box the user describes something in, and a button that asks the AI to draft it.
function AIRequestCard({ title, askName, label, hint, placeholder, buttonLabel, request, onResult, onCancel }) {
  const { aiAvailable } = useHealth();
  const [instruction, setInstruction] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      onResult(await request(instruction, name));
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title={title}>
      {!aiAvailable && (
        <div className="mb-4">
          <Notice tone="warning" title="Needs the AI">
            This needs an Anthropic API key, which isn't set yet. You can still add and edit rules by hand, or upload a .md file.
          </Notice>
        </div>
      )}
      <div className="space-y-4">
        {askName && (
          <Field label="Name of the document type" required>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Data Migration Plan" />
          </Field>
        )}
        <Field label={label} required hint={hint}>
          <textarea className="input min-h-28" value={instruction} onChange={(e) => setInstruction(e.target.value)} placeholder={placeholder} />
        </Field>
      </div>
      {error && <div className="mt-4"><ErrorMessage error={error} title="Couldn't get a draft from the AI" /></div>}
      <div className="mt-4 flex gap-2">
        <Button icon="sparkles" onClick={submit} disabled={busy || !instruction.trim() || (askName && !name.trim())}>
          {busy ? "Drafting… (can take up to a minute)" : buttonLabel}
        </Button>
        {onCancel && <Button variant="secondary" onClick={onCancel}>Cancel</Button>}
      </div>
    </Card>
  );
}

// New document type: the AI drafts all of its rules.
export function PromptRules({ onPreview, onCancel }) {
  return (
    <AIRequestCard
      title="Describe the new document type"
      askName
      label="What must a good document of this type contain?"
      hint="The AI drafts about 10 rules. You can edit them before saving."
      placeholder="e.g. A data migration plan must map every source field to a target field, define data quality checks, describe reconciliation, include a rollback plan, and name an owner for each step."
      buttonLabel="Draft rules with AI"
      request={(instruction, name) => api.post("/api/document-types/prompt-preview", { instruction, display_name: name })}
      onResult={onPreview}
      onCancel={onCancel}
    />
  );
}

// One rule: describe a new rule (rule = null), or describe how to change an existing one.
// onDraft receives { rule, original, summary } from the backend.
export function RuleAIDraft({ docKey, rule, onDraft, onCancel }) {
  return (
    <AIRequestCard
      title={rule ? `Change ${rule.id} "${rule.title}" with AI` : "Add a rule with AI"}
      label={rule ? "How should this rule change?" : "Describe the rule"}
      hint="You'll see the draft before anything is saved, and can edit it."
      placeholder={
        rule
          ? "e.g. Make it stricter: every objective needs a target value and a date. Make it critical."
          : "e.g. The document must say how long data is kept and who approves deleting it."
      }
      buttonLabel={rule ? "Draft the change" : "Draft the rule"}
      request={(instruction) => api.post(`/api/document-types/${docKey}/rules/draft`, { instruction, rule_id: rule ? rule.id : null })}
      onResult={onDraft}
      onCancel={onCancel}
    />
  );
}
