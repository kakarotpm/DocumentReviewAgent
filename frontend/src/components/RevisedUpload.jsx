// "Upload revised version": adds Version N+1 to a document and opens its review.
// If the type's rulebook has Excel rules (Part B), the workbook can be uploaded too. It isn't carried over
// from the previous version, so `previousWorkbook` (its file name) pre-ticks the box as a reminder.
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, useFetch } from "../lib/api";
import FileDropzone from "./FileDropzone";
import WorkbookUpload from "./WorkbookUpload";
import { Button, Card, ErrorMessage } from "./ui";

export default function RevisedUpload({ documentId, nextVersion, typeKey, previousWorkbook, onCancel }) {
  const navigate = useNavigate();
  const docType = useFetch(`/api/document-types/${typeKey}`);
  const [file, setFile] = useState(null);
  const [wantWorkbook, setWantWorkbook] = useState(Boolean(previousWorkbook));
  const [workbook, setWorkbook] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const hasExcelRules = Boolean(docType.data?.has_excel_rules);
  const useWorkbook = hasExcelRules && wantWorkbook;

  const submit = async () => {
    setBusy(true);
    setError(null);
    const form = new FormData();
    form.append("file", file);
    if (useWorkbook) form.append("workbook", workbook);
    try {
      const result = await api.upload(`/api/documents/${documentId}/versions`, form);
      navigate(`/reviews/${result.review_id}`);
    } catch (e) {
      setError(e);
      setBusy(false);
    }
  };

  return (
    <Card title={`Upload revised version (v${nextVersion})`}>
      <p className="mb-4 text-sm text-slate-600 dark:text-slate-400">
        It's reviewed against the latest rulebook, and the results show how the score changed from the previous version.
      </p>
      <FileDropzone file={file} onChange={setFile} />
      {hasExcelRules && (
        <WorkbookUpload
          wanted={wantWorkbook}
          onWantedChange={setWantWorkbook}
          file={workbook}
          onFileChange={setWorkbook}
          note={previousWorkbook && `The previous version was reviewed with "${previousWorkbook}". Workbooks aren't carried over, so choose it again (or its updated copy).`}
        />
      )}
      {error && <div className="mt-4"><ErrorMessage error={error} title="The revised version couldn't be uploaded" /></div>}
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <Button icon="upload" onClick={submit} disabled={!file || (useWorkbook && !workbook) || busy}>{busy ? "Uploading…" : "Upload and review"}</Button>
        {onCancel && <Button variant="secondary" onClick={onCancel}>Cancel</Button>}
        {file && useWorkbook && !workbook && <span className="text-sm text-slate-500">Add the Excel workbook (or untick the box) to continue.</span>}
      </div>
    </Card>
  );
}
