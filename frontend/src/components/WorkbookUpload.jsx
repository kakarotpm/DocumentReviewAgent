// "Also upload the Excel workbook": shown on New Review and revised uploads when the type's rulebook has Excel rules (Part B).
import FileDropzone from "./FileDropzone";

export default function WorkbookUpload({ wanted, onWantedChange, file, onFileChange, note }) {
  return (
    <div className="mt-4 rounded-lg border border-slate-200 p-4 dark:border-slate-800">
      <label className="flex items-start gap-2 text-sm">
        <input type="checkbox" checked={wanted} onChange={(e) => onWantedChange(e.target.checked)} className="mt-0.5 h-4 w-4 accent-indigo-600" />
        <span>
          <span className="font-medium">Also upload the Excel workbook</span>
          <span className="mt-0.5 block text-slate-500">
            This rulebook has Excel rules (Part B) that check the workbook's sheets, headers and completeness, not whether
            its data is correct. If you leave this unticked, only the document is reviewed and the Excel rules are left out
            (they don't count against the score).
          </span>
        </span>
      </label>
      {note && <p className="ml-6 mt-2 text-xs text-slate-500">{note}</p>}
      {wanted && <div className="ml-6 mt-3"><FileDropzone kind="workbook" file={file} onChange={onFileChange} /></div>}
    </div>
  );
}
