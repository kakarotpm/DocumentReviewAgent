// "Upload revised version": adds Version N+1 to a document and opens its review.
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import FileDropzone from "./FileDropzone";
import { Button, Card, ErrorMessage } from "./ui";

export default function RevisedUpload({ documentId, nextVersion, onCancel }) {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const submit = async () => {
    setBusy(true);
    setError(null);
    const form = new FormData();
    form.append("file", file);
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
      {error && <div className="mt-4"><ErrorMessage error={error} title="The revised version couldn't be uploaded" /></div>}
      <div className="mt-4 flex gap-2">
        <Button icon="upload" onClick={submit} disabled={!file || busy}>{busy ? "Uploading…" : "Upload and review"}</Button>
        {onCancel && <Button variant="secondary" onClick={onCancel}>Cancel</Button>}
      </div>
    </Card>
  );
}
