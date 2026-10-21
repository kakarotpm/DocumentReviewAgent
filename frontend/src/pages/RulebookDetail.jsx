// One rulebook: view its rules; add, edit or delete a rule by hand or with AI; upload/download .md; see its history.
import { useState } from "react";
import { useParams } from "react-router-dom";
import ChangePreview from "../components/ChangePreview";
import RuleEditor from "../components/RuleEditor";
import RuleList from "../components/RuleList";
import { MarkdownUpload, RuleAIDraft } from "../components/RulebookSources";
import { Badge, Button, Card, EmptyState, ErrorMessage, Notice, PageHeader, Spinner } from "../components/ui";
import { api, useFetch } from "../lib/api";
import { formatDateTime, idPrefix, nextRuleId } from "../lib/format";

const RULE_FIELDS = ["title", "weight", "critical", "check", "pass_example", "fail_example"];

// A one-rule change in the shape ChangePreview expects (the same shape the backend uses).
function oneRuleDiff({ added = [], removed = [], before = null, after = null }) {
  const changed = before && after
    ? [{ rule_id: after.id, before, after, changed_fields: RULE_FIELDS.filter((f) => (before[f] || null) !== (after[f] || null)) }]
    : [];
  return { added, removed, changed, settings_changed: [] };
}

function toRulebook(detail) {
  const { key, display_name, description, pass_threshold, rules } = detail;
  return { doc_type: key, display_name, description, pass_threshold, rules };
}

export default function RulebookDetail() {
  const { key } = useParams();
  const { data: detail, error, loading, reload } = useFetch(`/api/document-types/${key}`);
  const history = useFetch(`/api/document-types/${key}/versions`);
  const [mode, setMode] = useState("view"); // view | edit | upload | ai | preview
  const [tab, setTab] = useState("rules");
  const [preview, setPreview] = useState(null);
  const [editStart, setEditStart] = useState(null);
  const [openRuleId, setOpenRuleId] = useState(null); // rule to expand when the editor opens
  const [aiRule, setAiRule] = useState(null); // rule the AI is changing; null = AI adds a new rule
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [savedMessage, setSavedMessage] = useState("");

  if (loading && !detail) return <Spinner />;
  if (error) {
    return error.status === 404 ? (
      <EmptyState icon="book" title="Rulebook not found" action={<Button to="/rulebooks">Back to Rulebooks</Button>}>
        There's no document type called "{key}".
      </EmptyState>
    ) : (
      <ErrorMessage error={error} title="Couldn't load this rulebook" onRetry={reload} />
    );
  }

  const go = (next) => {
    setMode(next);
    setSaveError(null);
    setSavedMessage("");
  };

  const save = async ({ rulebook, changed_by, change_note }) => {
    setSaving(true);
    setSaveError(null);
    try {
      const updated = await api.put(`/api/document-types/${key}`, { rulebook, changed_by, change_note });
      reload();
      history.reload();
      setMode("view");
      setSavedMessage(`Saved as version ${updated.version}. New reviews will use these rules; past reviews keep the rules they used.`);
    } catch (e) {
      setSaveError(e);
    } finally {
      setSaving(false);
    }
  };

  const showPreview = (result) => {
    setPreview(result);
    go("preview");
  };

  const editFrom = (rulebook, ruleId = null) => {
    setEditStart(rulebook);
    setOpenRuleId(ruleId);
    go("edit");
  };

  const current = () => toRulebook(detail);

  // Add a blank rule at the end and open the editor on it.
  const addRule = () => {
    const rb = current();
    const id = nextRuleId(rb.rules, idPrefix(rb.display_name));
    const blank = { id, title: "", weight: "medium", critical: false, check: "", pass_example: "", fail_example: "" };
    editFrom({ ...rb, rules: [...rb.rules, blank] }, id);
  };

  const askAI = (rule) => {
    setAiRule(rule);
    go("ai");
  };

  // The AI's draft: show it as a change to review before saving.
  const showDraft = ({ rule, original, summary }) => {
    const rb = current();
    const rules = original ? rb.rules.map((r) => (r.id === original.id ? rule : r)) : [...rb.rules, rule];
    const diff = original ? oneRuleDiff({ before: original, after: rule }) : oneRuleDiff({ added: [rule] });
    showPreview({ mode: "update", rulebook: { ...rb, rules }, diff, summary });
  };

  const deleteRule = (rule) => {
    const rb = current();
    showPreview({
      mode: "update",
      rulebook: { ...rb, rules: rb.rules.filter((r) => r.id !== rule.id) },
      diff: oneRuleDiff({ removed: [rule] }),
      summary: `Delete ${rule.id} "${rule.title}". Past reviews keep the rules they used.`,
    });
  };

  const criticalCount = detail.rules.filter((r) => r.critical).length;

  return (
    <>
      <PageHeader
        back={{ to: "/rulebooks", label: "Rulebooks" }}
        title={detail.display_name}
        subtitle={
          <>
            {detail.description}
            <span className="mt-1 block">
              Version {detail.version} · updated {formatDateTime(detail.updated_at)} by {detail.updated_by} · pass threshold {detail.pass_threshold} ·{" "}
              {detail.rules.length} rules, {criticalCount} critical
            </span>
          </>
        }
        actions={
          mode === "view" && (
            <>
              <Button icon="plus" onClick={addRule}>Add rule</Button>
              <Button variant="secondary" icon="sparkles" onClick={() => askAI(null)}>Add rule with AI</Button>
              <Button variant="secondary" icon="pencil" onClick={() => editFrom(current())}>Edit all</Button>
              <Button variant="secondary" icon="upload" onClick={() => go("upload")}>Upload .md</Button>
              <a
                href={`/api/document-types/${key}/export`}
                download={`${key}.md`}
                className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
              >
                Download .md
              </a>
            </>
          )
        }
      />

      {savedMessage && <div className="mb-5"><Notice tone="success" icon="check-circle">{savedMessage}</Notice></div>}

      {mode === "edit" && (
        <RuleEditor initial={editStart} openRuleId={openRuleId} onSave={save} onCancel={() => go("view")} saving={saving} error={saveError} />
      )}
      {mode === "ai" && <RuleAIDraft docKey={key} rule={aiRule} onDraft={showDraft} onCancel={() => go("view")} />}
      {mode === "upload" && <MarkdownUpload targetKey={key} onPreview={showPreview} onCancel={() => go("view")} />}
      {mode === "preview" && preview && (
        <ChangePreview preview={preview} onSave={save} onEdit={editFrom} onCancel={() => go("view")} saving={saving} error={saveError} />
      )}

      {mode === "view" && (
        <>
          <div className="mb-4 flex gap-1 border-b border-slate-200 dark:border-slate-800" role="tablist">
            {[["rules", `Rules (${detail.rules.length})`], ["history", "Version history"]].map(([id, label]) => (
              <button
                key={id}
                role="tab"
                aria-selected={tab === id}
                onClick={() => setTab(id)}
                className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium ${
                  tab === id ? "border-indigo-600 text-indigo-700 dark:text-indigo-300" : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          {tab === "rules" && (
            <RuleList
              rules={detail.rules}
              renderActions={(rule) => (
                <>
                  <Button variant="ghost" icon="pencil" onClick={() => editFrom(current(), rule.id)}>Edit</Button>
                  <Button variant="ghost" icon="sparkles" onClick={() => askAI(rule)}>Change with AI</Button>
                  <Button variant="danger" icon="trash" onClick={() => deleteRule(rule)} className="ml-auto">Delete</Button>
                </>
              )}
            />
          )}
          {tab === "history" && (
            <Card>
              {history.loading && <Spinner />}
              <ErrorMessage error={history.error} onRetry={history.reload} />
              {history.data && (
                <ol className="divide-y divide-slate-200 dark:divide-slate-800">
                  {history.data.map((v) => (
                    <li key={v.version} className="flex flex-wrap items-baseline gap-x-3 gap-y-1 py-3 text-sm">
                      <Badge tone={v.version === detail.version ? "indigo" : "slate"}>v{v.version}{v.version === detail.version && " · current"}</Badge>
                      <span className="font-medium">{v.changed_by}</span>
                      <span className="text-slate-500">{formatDateTime(v.created_at)}</span>
                      <span className="text-slate-500">· {v.rule_count} rules</span>
                      {v.change_note && <span className="w-full text-slate-600 dark:text-slate-400">"{v.change_note}"</span>}
                    </li>
                  ))}
                </ol>
              )}
            </Card>
          )}
        </>
      )}
    </>
  );
}
