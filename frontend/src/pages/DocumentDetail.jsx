// One document: its status and a timeline of every version with its score.
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import RevisedUpload from "../components/RevisedUpload";
import { Badge, Button, Card, DocumentStatusBadge, EmptyState, ErrorMessage, PageHeader, PassFailBadge, Spinner } from "../components/ui";
import { useFetch } from "../lib/api";
import { formatDateTime } from "../lib/format";

function ReviewLine({ review }) {
  if (review.status === "complete") {
    return (
      <span className="flex flex-wrap items-center gap-2">
        <span className="text-lg font-semibold">{review.score}</span>
        <PassFailBadge passed={review.passed} />
      </span>
    );
  }
  if (review.status === "error") return <Badge tone="amber" icon="alert">Review failed</Badge>;
  return <Badge icon="clock">In review</Badge>;
}

export default function DocumentDetail() {
  const { documentId } = useParams();
  const { data: doc, error, loading, reload } = useFetch(`/api/documents/${documentId}`);
  const [showUpload, setShowUpload] = useState(false);

  if (loading && !doc) return <Spinner />;
  if (error) {
    return error.status === 404 ? (
      <EmptyState icon="search" title="Document not found" action={<Button to="/documents">Back to Documents</Button>} />
    ) : (
      <ErrorMessage error={error} title="Couldn't load this document" onRetry={reload} />
    );
  }

  const latest = doc.versions[doc.versions.length - 1];
  return (
    <>
      <PageHeader
        back={{ to: "/documents", label: "Documents" }}
        title={doc.title}
        subtitle={<>{doc.document_type_name}{doc.project_name && <> · {doc.project_name}</>} · uploaded by {doc.uploaded_by}</>}
        actions={
          <>
            <DocumentStatusBadge status={doc.status} />
            <Button icon="upload" onClick={() => setShowUpload((v) => !v)}>Upload revised version</Button>
          </>
        }
      />
      {showUpload && <div className="mb-5"><RevisedUpload documentId={doc.id} nextVersion={latest.version_number + 1} typeKey={doc.document_type} previousWorkbook={latest.workbook_filename} onCancel={() => setShowUpload(false)} /></div>}

      <Card title="Versions">
        <ol className="relative space-y-6 border-l border-slate-200 pl-6 dark:border-slate-700">
          {[...doc.versions].reverse().map((v) => {
            const review = v.reviews[v.reviews.length - 1];
            return (
              <li key={v.id} className="relative">
                <span className="absolute -left-[31px] top-1 h-3 w-3 rounded-full border-2 border-white bg-indigo-500 dark:border-slate-900" />
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-medium">Version {v.version_number} <span className="font-normal text-slate-500">· {v.original_filename}{v.workbook_filename && <> + {v.workbook_filename}</>}</span></p>
                    <p className="text-sm text-slate-500">Uploaded {formatDateTime(v.uploaded_at)}{review && <> · rulebook v{review.rulebook_version}</>}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    {review ? <ReviewLine review={review} /> : <Badge>Not reviewed</Badge>}
                    {review && <Link to={`/reviews/${review.id}`} className="text-sm font-medium text-indigo-700 hover:underline dark:text-indigo-400">View results</Link>}
                  </div>
                </div>
                {v.reviews.length > 1 && (
                  <p className="mt-1 text-xs text-slate-500">
                    Reviewed {v.reviews.length} times. Earlier:{" "}
                    {v.reviews.slice(0, -1).map((r, i) => (
                      <span key={r.id}>{i > 0 && ", "}<Link to={`/reviews/${r.id}`} className="underline">{r.status === "complete" ? r.score : r.status}</Link></span>
                    ))}
                  </p>
                )}
              </li>
            );
          })}
        </ol>
      </Card>
    </>
  );
}
