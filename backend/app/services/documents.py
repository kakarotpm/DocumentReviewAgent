"""Creating documents from uploads, adding revised versions, and listing documents."""

from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Document, DocumentType, DocumentVersion, Review
from app.schemas import DocumentDetail, DocumentListItem, ReviewSummary, UploadResult, VersionSummary
from app.services.extraction import extract_text, extract_workbook
from app.services.status import document_status

PREVIEW_CHARS = 1000
STATUSES = ["Passed", "Failed", "Corrected", "In review", "Error"]
SORT_FIELDS = {
    "title": lambda d: d.title.lower(),
    "type": lambda d: d.document_type_name.lower(),
    "project": lambda d: d.project_name.lower(),
    "uploaded_by": lambda d: d.uploaded_by.lower(),
    "score": lambda d: -1 if d.latest_score is None else d.latest_score,
    "status": lambda d: d.status,
    "versions": lambda d: d.versions,
    "updated": lambda d: d.updated_at,
}


class UploadError(ValueError):
    """The upload can't be accepted. The message tells the user what to do next."""


def _read_workbook(doc_type: DocumentType, workbook: tuple[str, bytes] | None) -> tuple[str | None, str | None]:
    """Check and read the optional Excel workbook. Returns (filename, text), or (None, None) if there isn't one."""
    if workbook is None:
        return None, None
    if not any(r.get("part") == "excel" for r in doc_type.latest_version.rules_json):
        raise UploadError(
            f"{doc_type.display_name} has no Excel rules (Part B), so a workbook can't be reviewed. "
            "Remove the workbook, or add Part B rules to the rulebook first."
        )
    filename, data = workbook
    return filename, extract_workbook(filename, data)  # raises ExtractionError with a friendly message


def _upload_result(version: DocumentVersion, review: Review) -> UploadResult:
    return UploadResult(
        document_id=version.document.id,
        version_id=version.id,
        version_number=version.version_number,
        review_id=review.id,
        review_status=review.status,
        file_type=version.file_type,
        extracted_characters=len(version.extracted_text),
        extracted_text_preview=version.extracted_text[:PREVIEW_CHARS],
        workbook_filename=version.workbook_filename,
    )


def create_document(
    session: Session,
    *,
    filename: str,
    data: bytes,
    document_type_key: str,
    uploaded_by: str,
    title: str = "",
    project_name: str = "",
    workbook: tuple[str, bytes] | None = None,
) -> UploadResult:
    """Extract the file's text and create the Document, Version 1, and a queued Review.

    `workbook` is an optional (filename, bytes) Excel file, reviewed against the rulebook's Part B.
    Raises UploadError or ExtractionError (both have user-friendly messages).
    """
    uploaded_by = uploaded_by.strip()
    if not uploaded_by:
        raise UploadError("Please enter your name.")
    doc_type = session.scalar(select(DocumentType).where(DocumentType.key == document_type_key))
    if doc_type is None:
        raise UploadError(f"Unknown document type '{document_type_key}'. Please choose a type from the list.")

    file_type, text = extract_text(filename, data)  # raises ExtractionError with a friendly message
    workbook_filename, workbook_text = _read_workbook(doc_type, workbook)

    document = Document(
        title=title.strip() or Path(filename).stem,
        document_type=doc_type,
        project_name=project_name.strip(),
        uploaded_by=uploaded_by,
    )
    version = DocumentVersion(
        version_number=1,
        original_filename=filename,
        file_type=file_type,
        extracted_text=text,
        workbook_filename=workbook_filename,
        workbook_text=workbook_text,
    )
    document.versions.append(version)
    review = Review(document_version=version, rulebook_version=doc_type.latest_version, status="queued")
    session.add_all([document, review])
    session.commit()
    return _upload_result(version, review)


def add_version(
    session: Session,
    *,
    document_id: int,
    filename: str,
    data: bytes,
    workbook: tuple[str, bytes] | None = None,
) -> UploadResult | None:
    """Add a revised version to a document and queue its review against the latest rulebook.

    `workbook` is an optional (filename, bytes) Excel file, as in create_document. A workbook
    isn't carried over from the previous version: upload it again to have it reviewed.
    Returns None if the document doesn't exist. Raises UploadError or ExtractionError for unusable files.
    """
    document = session.get(Document, document_id)
    if document is None:
        return None
    file_type, text = extract_text(filename, data)
    workbook_filename, workbook_text = _read_workbook(document.document_type, workbook)
    version = DocumentVersion(
        version_number=document.versions[-1].version_number + 1,
        original_filename=filename,
        file_type=file_type,
        extracted_text=text,
        workbook_filename=workbook_filename,
        workbook_text=workbook_text,
    )
    document.versions.append(version)
    review = Review(document_version=version, rulebook_version=document.document_type.latest_version, status="queued")
    session.add(review)
    session.commit()
    return _upload_result(version, review)


def _status_of(document: Document) -> str:
    pairs = []
    for version in document.versions:
        if version.reviews:
            latest = version.reviews[-1]
            pairs.append((latest.status, latest.passed))
    return document_status(pairs)


def _latest_review(document: Document) -> Review | None:
    reviews = document.versions[-1].reviews
    return reviews[-1] if reviews else None


def get_document(session: Session, document_id: int) -> DocumentDetail | None:
    """A document with all its versions and their reviews, or None if it doesn't exist."""
    document = session.get(Document, document_id)
    if document is None:
        return None
    return DocumentDetail(
        id=document.id,
        title=document.title,
        document_type=document.document_type.key,
        document_type_name=document.document_type.display_name,
        project_name=document.project_name,
        uploaded_by=document.uploaded_by,
        status=_status_of(document),
        created_at=document.created_at,
        versions=[
            VersionSummary(
                id=v.id,
                version_number=v.version_number,
                original_filename=v.original_filename,
                file_type=v.file_type,
                extracted_characters=len(v.extracted_text),
                workbook_filename=v.workbook_filename,
                uploaded_at=v.uploaded_at,
                reviews=[
                    ReviewSummary(
                        id=r.id,
                        status=r.status,
                        score=r.score,
                        passed=r.passed,
                        rulebook_version=r.rulebook_version.version_number,
                        created_at=r.created_at,
                    )
                    for r in v.reviews
                ],
            )
            for v in document.versions
        ],
    )


def list_documents(
    session: Session,
    *,
    search: str = "",
    document_type: str = "",
    status: str = "",
    project: str = "",
    date_from: date | None = None,
    date_to: date | None = None,
    sort: str = "updated",
    descending: bool = True,
) -> list[DocumentListItem]:
    """Documents for the Documents table, filtered and sorted.

    Filtering happens in Python: simple to read, and fast enough for thousands of documents.
    """
    items = []
    for document in session.scalars(select(Document)):
        latest = _latest_review(document)
        item = DocumentListItem(
            id=document.id,
            title=document.title,
            document_type_key=document.document_type.key,
            document_type_name=document.document_type.display_name,
            project_name=document.project_name,
            uploaded_by=document.uploaded_by,
            latest_score=latest.score if latest else None,
            latest_review_id=latest.id if latest else None,
            status=_status_of(document),
            versions=len(document.versions),
            updated_at=document.updated_at,
        )
        if search and search.lower() not in item.title.lower():
            continue
        if document_type and item.document_type_key != document_type:
            continue
        if status and item.status != status:
            continue
        if project and item.project_name != project:
            continue
        if date_from and item.updated_at.date() < date_from:
            continue
        if date_to and item.updated_at.date() > date_to:
            continue
        items.append(item)
    items.sort(key=SORT_FIELDS.get(sort, SORT_FIELDS["updated"]), reverse=descending)
    return items


def list_projects(session: Session) -> list[str]:
    """Distinct project names, for the filter dropdowns."""
    names = session.scalars(select(Document.project_name).distinct().order_by(Document.project_name))
    return [name for name in names if name]
