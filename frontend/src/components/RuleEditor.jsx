// Edit a rulebook by hand: its settings, and every rule's text, weight and critical flag.
// Used for editing an existing type, creating a new one, and tweaking an AI or .md preview before saving.
import { useState } from "react";
import { idPrefix, keyFromName, nextRuleId, rememberName, savedName } from "../lib/format";
import Icon from "./Icon";
import { Button, Card, ErrorMessage, Field } from "./ui";

export default function RuleEditor({ initial, isNew = false, onSave, onCancel, saving, error, saveLabel = "Save changes" }) {
  const [rulebook, setRulebook] = useState(initial);
  const [openId, setOpenId] = useState(null); // the rule whose details are expanded
  const [name, setName] = useState(savedName());
  const [note, setNote] = useState("");

  const criticalCount = rulebook.rules.filter((r) => r.critical).length;

  const setField = (field, value) => {
    setRulebook((rb) => {
      const updated = { ...rb, [field]: value };
      if (isNew && field === "display_name") updated.doc_type = keyFromName(value);
      return updated;
    });
  };

  const updateRule = (id, field, value) =>
    setRulebook((rb) => ({ ...rb, rules: rb.rules.map((r) => (r.id === id ? { ...r, [field]: value } : r)) }));

  const deleteRule = (id) => setRulebook((rb) => ({ ...rb, rules: rb.rules.filter((r) => r.id !== id) }));

  const addRule = () => {
    const id = nextRuleId(rulebook.rules, idPrefix(rulebook.display_name));
    const rule = { id, title: "", weight: "medium", critical: false, check: "", pass_example: "", fail_example: "" };
    setRulebook((rb) => ({ ...rb, rules: [...rb.rules, rule] }));
    setOpenId(id);
  };

  const submit = (event) => {
    event.preventDefault();
    rememberName(name);
    const clean = {
      ...rulebook,
      pass_threshold: Number(rulebook.pass_threshold),
      rules: rulebook.rules.map((r) => ({ ...r, pass_example: r.pass_example || null, fail_example: r.fail_example || null })),
    };
    onSave({ rulebook: clean, changed_by: name, change_note: note });
  };

  return (
    <form onSubmit={submit} className="space-y-5">
      <Card title="Document type">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Name" required>
            <input className="input" value={rulebook.display_name} onChange={(e) => setField("display_name", e.target.value)} placeholder="e.g. Data Migration Plan" required />
          </Field>
          <Field label="Pass threshold" hint="Score needed to pass (0–100). Critical rules must also be met.">
            <input className="input" type="number" min="0" max="100" value={rulebook.pass_threshold} onChange={(e) => setField("pass_threshold", e.target.value)} required />
          </Field>
          <div className="sm:col-span-2">
            <Field label="Description" hint="One line shown on the New Review screen.">
              <input className="input" value={rulebook.description} onChange={(e) => setField("description", e.target.value)} />
            </Field>
          </div>
        </div>
      </Card>

      <Card
        title={`Rules (${rulebook.rules.length})`}
        actions={<span className="text-sm text-slate-500">{criticalCount} critical</span>}
      >
        {rulebook.rules.length === 0 && (
          <p className="mb-4 text-sm text-slate-500">No rules yet. Add the first one below.</p>
        )}
        <ol className="space-y-2">
          {rulebook.rules.map((rule) => {
            const open = openId === rule.id;
            return (
              <li key={rule.id} className="rounded-lg border border-slate-200 dark:border-slate-800">
                <div className="flex items-center gap-3 p-3">
                  <button type="button" onClick={() => setOpenId(open ? null : rule.id)} className="flex min-w-0 flex-1 items-center gap-3 text-left" aria-expanded={open}>
                    <Icon name="chevron" className={`h-4 w-4 shrink-0 text-slate-400 transition-transform ${open ? "" : "-rotate-90"}`} />
                    <span className="font-mono text-xs text-slate-500">{rule.id}</span>
                    <span className="truncate text-sm font-medium">{rule.title || <em className="text-slate-400">Untitled rule</em>}</span>
                  </button>
                  <select
                    aria-label={`Weight for ${rule.id}`}
                    className="input w-auto py-1"
                    value={rule.weight}
                    onChange={(e) => updateRule(rule.id, "weight", e.target.value)}
                  >
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                  <label className="flex items-center gap-1.5 whitespace-nowrap text-sm">
                    <input type="checkbox" checked={rule.critical} onChange={(e) => updateRule(rule.id, "critical", e.target.checked)} className="h-4 w-4 accent-red-600" />
                    Critical
                  </label>
                  <button type="button" onClick={() => deleteRule(rule.id)} className="rounded p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/50" title={`Delete ${rule.id}`}>
                    <Icon name="trash" />
                  </button>
                </div>
                {open && (
                  <div className="grid gap-3 border-t border-slate-200 p-4 sm:grid-cols-2 dark:border-slate-800">
                    <div className="sm:col-span-2">
                      <Field label="Title" required>
                        <input className="input" value={rule.title} onChange={(e) => updateRule(rule.id, "title", e.target.value)} placeholder="e.g. Measurable business objectives" />
                      </Field>
                    </div>
                    <div className="sm:col-span-2">
                      <Field label="What to check" required hint="Exactly what the reviewer looks for, including what counts as only partly met.">
                        <textarea className="input min-h-20" value={rule.check} onChange={(e) => updateRule(rule.id, "check", e.target.value)} />
                      </Field>
                    </div>
                    <Field label="Example that passes">
                      <textarea className="input min-h-16" value={rule.pass_example || ""} onChange={(e) => updateRule(rule.id, "pass_example", e.target.value)} />
                    </Field>
                    <Field label="Example that fails">
                      <textarea className="input min-h-16" value={rule.fail_example || ""} onChange={(e) => updateRule(rule.id, "fail_example", e.target.value)} />
                    </Field>
                    {rule.critical && (
                      <p className="text-xs text-red-700 sm:col-span-2 dark:text-red-400">
                        Critical: if this rule is Not Met, the document fails whatever its score.
                      </p>
                    )}
                  </div>
                )}
              </li>
            );
          })}
        </ol>
        <Button variant="secondary" icon="plus" onClick={addRule} className="mt-3">
          Add rule
        </Button>
      </Card>

      <Card title="Save">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Your name" required hint="Recorded in the version history.">
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
          </Field>
          <Field label="What changed and why" hint="Optional, shown in the version history.">
            <input className="input" value={note} onChange={(e) => setNote(e.target.value)} placeholder="e.g. Made risks critical after Q3 audit" />
          </Field>
        </div>
        {error && <div className="mt-4"><ErrorMessage error={error} title="Not saved" /></div>}
        <div className="mt-4 flex flex-wrap gap-2">
          <Button type="submit" disabled={saving || rulebook.rules.length === 0} icon="check">
            {saving ? "Saving…" : saveLabel}
          </Button>
          {onCancel && <Button variant="secondary" onClick={onCancel}>Cancel</Button>}
        </div>
      </Card>
    </form>
  );
}
