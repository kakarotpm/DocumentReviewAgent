// Drag-and-drop (or click to pick) a document. Checks type and size before uploading.
import { useState } from "react";
import { formatSize } from "../lib/format";
import Icon from "./Icon";

const ACCEPTED = [".docx", ".pdf", ".md", ".txt"];
const MAX_BYTES = 10 * 1024 * 1024;

export function checkFile(file) {
  const name = file.name.toLowerCase();
  if (!ACCEPTED.some((ext) => name.endsWith(ext))) {
    return `"${file.name}" isn't a supported file type. Please choose a .docx, .pdf, .md or .txt file.`;
  }
  if (file.size > MAX_BYTES) return `"${file.name}" is ${formatSize(file.size)}. The limit is 10 MB.`;
  if (file.size === 0) return `"${file.name}" is empty.`;
  return null;
}

export default function FileDropzone({ file, onChange }) {
  const [dragging, setDragging] = useState(false);
  const [problem, setProblem] = useState(null);

  const pick = (picked) => {
    if (!picked) return;
    const issue = checkFile(picked);
    setProblem(issue);
    onChange(issue ? null : picked);
  };

  if (file) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-800/50">
        <Icon name="file" className="h-6 w-6 text-indigo-600" />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{file.name}</p>
          <p className="text-xs text-slate-500">{formatSize(file.size)}</p>
        </div>
        <button type="button" onClick={() => onChange(null)} className="rounded p-1.5 text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-700" title="Remove file">
          <Icon name="x" />
        </button>
      </div>
    );
  }

  return (
    <div>
      <label
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); pick(e.dataTransfer.files[0]); }}
        className={`flex cursor-pointer flex-col items-center rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors ${
          dragging ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30" : "border-slate-300 hover:border-indigo-400 dark:border-slate-700"
        }`}
      >
        <Icon name="upload" className="h-8 w-8 text-slate-400" />
        <span className="mt-2 text-sm font-medium">Drag a file here, or click to choose</span>
        <span className="mt-1 text-xs text-slate-500">.docx, .pdf (text-based), .md or .txt · up to 10 MB</span>
        <input type="file" accept={ACCEPTED.join(",")} className="sr-only" onChange={(e) => pick(e.target.files[0])} />
      </label>
      {problem && <p className="mt-2 text-sm text-red-700 dark:text-red-400" role="alert">{problem}</p>}
    </div>
  );
}
