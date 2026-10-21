// Shows what an uploaded .md file or an AI prompt would change, before anything is saved.
import { useState } from "react";
import { rememberName, savedName, WEIGHT_LABELS } from "../lib/format";
import RuleList from "./RuleList";
import { Badge, Button, Card, CriticalBadge, ErrorMessage, Field, Notice, WeightBadge } from "./ui";

const FIELD_LABELS = {
  title: "Title", weight: "Weight", critical: "Critical",
  check: "What to check", pass_example: "Pass example", fail_example: "Fail example",
  display_name: "Name", description: "Description", pass_threshold: "Pass threshold",
};

function show(field, value) {
  if (field === "weight") return WEIGHT_LABELS[value];
  if (field === "critical") return value ? "Yes" : "No";
  return value || "(empty)";
}

function RuleHeading({ rule }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="font-mono text-xs text-slate-500">{rule.id}</span>
      <span className="font-medium">{rule.title}</span>
      {rule.critical && <CriticalBadge />}
      <WeightBadge weight={rule.weight} />
    </div>
  );
}

export default function ChangePreview({ preview, onSave, onEdit, onCancel, saving, error, showListedOption = false }) {
  const [name, setName] = useState(savedName());
  const [note, setNote] = useState("");
  const [listed, setListed] = useState(true);
  const { mode, diff, rulebook, summary } = preview;
  const nothingChanged =
    mode === "update" && !diff.added.length && !diff.removed.length && !diff.changed.length && !diff.settings_changed.length;

  const save = () => {
    rememberName(name);
    onSave({ rulebook, changed_by: name, change_note: note, listed });
  };

  return (
    <div className="space-y-5">
      <Card title={mode === "new" ? `New document type: ${rulebook.display_name}` : "Changes to review"}>
        {summary && <p className="mb-4 text-sm text-slate-600 dark:text-slate-400">{summary}</p>}
        <Notice tone="info">Nothing has been saved yet. Check the changes, then save, edit them first, or cancel.</Notice>

        {mode === "new" && (
          <div className="mt-4">
            <p className="mb-3 text-sm text-slate-600 dark:text-slate-400">
              {rulebook.rules.length} rules · pass threshold {rulebook.pass_threshold}
              {rulebook.description && <> · {rulebook.description}</>}
            </p>
            <RuleList rules={rulebook.rules} />
          </div>
        )}

        {mode === "update" && nothingChanged && (
          <div className="mt-4"><Notice tone="warning">This matches the current rulebook exactly, so there's nothing to save.</Notice></div>
        )}

        {mode === "update" && !nothingChanged && (
          <div className="mt-4 space-y-5">
            {diff.settings_changed.length > 0 && (
              <section>
                <h3 className="mb-2 text-sm font-semibold">Settings changed</h3>
                <ul className="space-y-1 text-sm">
                  {diff.settings_changed.map((f) => (
                    <li key={f}>{FIELD_LABELS[f]}: <strong>{show(f, rulebook[f])}</strong></li>
                  ))}
                </ul>
              </section>
            )}
            {diff.added.length > 0 && (
              <section>
                <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold"><Badge tone="green" icon="plus">Added</Badge> {diff.added.length} rule(s)</h3>
                <ul className="space-y-2">
                  {diff.added.map((rule) => (
                    <li key={rule.id} className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-3 text-sm dark:border-emerald-900 dark:bg-emerald-950/20">
                      <RuleHeading rule={rule} />
                      <p className="mt-1 text-slate-700 dark:text-slate-300">{rule.check}</p>
                    </li>
                  ))}
                </ul>
              </section>
            )}
            {diff.changed.length > 0 && (
              <section>
                <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold"><Badge tone="amber" icon="pencil">Changed</Badge> {diff.changed.length} rule(s)</h3>
                <ul className="space-y-2">
                  {diff.changed.map((change) => (
                    <li key={change.rule_id} className="rounded-lg border border-amber-200 bg-amber-50/50 p-3 text-sm dark:border-amber-900 dark:bg-amber-950/20">
                      <RuleHeading rule={change.after} />
                      <table className="mt-2 w-full text-left">
                        <tbody>
                          {change.changed_fields.filter((f) => f !== "category").map((f) => (
                            <tr key={f} className="align-top">
                              <th className="w-32 py-1 pr-3 font-medium text-slate-500">{FIELD_LABELS[f]}</th>
                              <td className="py-1 pr-3 text-slate-500 line-through">{show(f, change.before[f])}</td>
                              <td className="py-1">{show(f, change.after[f])}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </li>
                  ))}
                </ul>
              </section>
            )}
            {diff.removed.length > 0 && (
              <section>
                <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold"><Badge tone="red" icon="trash">Removed</Badge> {diff.removed.length} rule(s)</h3>
                <ul className="space-y-2">
                  {diff.removed.map((rule) => (
                    <li key={rule.id} className="rounded-lg border border-red-200 bg-red-50/50 p-3 text-sm dark:border-red-900 dark:bg-red-950/20">
                      <RuleHeading rule={rule} />
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </div>
        )}
      </Card>

      {!nothingChanged && (
        <Card title="Save">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Your name" required hint="Recorded in the version history.">
              <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
            </Field>
            <Field label="What changed and why" hint="Optional.">
              <input className="input" value={note} onChange={(e) => setNote(e.target.value)} />
            </Field>
          </div>
          {showListedOption && mode === "new" && (
            <label className="mt-4 flex items-center gap-2 text-sm">
              <input type="checkbox" checked={listed} onChange={(e) => setListed(e.target.checked)} className="h-4 w-4 accent-indigo-600" />
              Save as a reusable type (show it in the type list for future reviews)
            </label>
          )}
          {error && <div className="mt-4"><ErrorMessage error={error} title="Not saved" /></div>}
          <div className="mt-4 flex flex-wrap gap-2">
            <Button icon="check" onClick={save} disabled={saving || !name.trim()}>{saving ? "Saving…" : "Save"}</Button>
            <Button variant="secondary" icon="pencil" onClick={() => onEdit(rulebook)}>Edit before saving</Button>
            <Button variant="ghost" onClick={onCancel}>Cancel</Button>
          </div>
        </Card>
      )}
      {nothingChanged && <Button variant="secondary" onClick={onCancel}>Back</Button>}
    </div>
  );
}
