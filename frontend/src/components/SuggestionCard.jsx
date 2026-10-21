// One suggestion: where, what's there now, what to put instead, why. Can be copied and marked done/dismissed.
import { useState } from "react";
import { api } from "../lib/api";
import Icon from "./Icon";

const STATES = [
  { id: "open", label: "Open" },
  { id: "done", label: "Done" },
  { id: "dismissed", label: "Dismissed" },
];

export default function SuggestionCard({ suggestion, rule }) {
  const [state, setState] = useState(suggestion.user_state);
  const [copied, setCopied] = useState(false);
  const [problem, setProblem] = useState("");

  const changeState = async (next) => {
    const previous = state;
    setState(next); // update straight away; undo if saving fails
    setProblem("");
    try {
      await api.patch(`/api/suggestions/${suggestion.id}`, { user_state: next });
    } catch (e) {
      setState(previous);
      setProblem(e.message);
    }
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(suggestion.proposed_text || suggestion.current_text || "");
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setProblem("Couldn't copy. Select the text and copy it manually.");
    }
  };

  return (
    <article className={`rounded-lg border border-slate-200 p-4 dark:border-slate-800 ${state !== "open" ? "opacity-60" : ""}`}>
      <header className="flex flex-wrap items-center gap-2 text-sm">
        <span className="font-mono text-xs text-slate-500">{rule.rule_id}</span>
        <span className="font-medium">{rule.title}</span>
        <span className="text-slate-500">· {suggestion.location}</span>
      </header>

      {suggestion.current_text && (
        <div className="mt-3">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{suggestion.type === "delete" ? "Remove" : "Current text"}</p>
          <blockquote className="mt-1 rounded-md bg-slate-100 p-2 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-300">
            {suggestion.current_text}
          </blockquote>
        </div>
      )}
      {suggestion.proposed_text && (
        <div className="mt-3">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{suggestion.type === "add" ? "Add" : "Replace with"}</p>
          <blockquote className="mt-1 whitespace-pre-line rounded-md bg-indigo-50 p-2 text-sm text-slate-800 dark:bg-indigo-950/40 dark:text-slate-200">
            {suggestion.proposed_text}
          </blockquote>
        </div>
      )}
      <p className="mt-3 text-sm text-slate-600 dark:text-slate-400"><strong className="font-medium">Why: </strong>{suggestion.rationale}</p>

      <footer className="mt-3 flex flex-wrap items-center gap-2">
        <button type="button" onClick={copy} className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-sm text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800">
          <Icon name={copied ? "check" : "copy"} /> {copied ? "Copied" : "Copy"}
        </button>
        <div className="ml-auto inline-flex rounded-md border border-slate-300 dark:border-slate-700" role="group" aria-label="Suggestion status">
          {STATES.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => changeState(s.id)}
              aria-pressed={state === s.id}
              className={`px-2.5 py-1 text-xs font-medium first:rounded-l-md last:rounded-r-md ${
                state === s.id ? "bg-slate-800 text-white dark:bg-slate-200 dark:text-slate-900" : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </footer>
      {problem && <p className="mt-2 text-sm text-red-700 dark:text-red-400">{problem}</p>}
    </article>
  );
}
