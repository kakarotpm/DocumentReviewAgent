"""Creating documents from uploads, and reading them back."""

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Document, DocumentType, DocumentVersion, Review
from app.schemas import DocumentDetail, ReviewSummary, UploadResult, VersionSummary
from app.services.extraction import extract_text

PREVIEW_CHARS = 1000


class UploadError(ValueError):
    """The upload can't be accepted. The message tells the user what to do next."""


def create_document(
    session: Session,
    *,
    filename: str,
    data: bytes,
    document_type_key: str,
    uploaded_by: str,
    title: str = "",
    project_name: str = "",
) -> UploadResult:
    """Extract the file's text and create the Document, Version 1, and a queued Review.

    Raises UploadError or ExtractionError (both have user-friendly messages).
    """
    uploaded_by = uploaded_by.strip()
    if not uploaded_by:
        raise UploadError("Please enter your name.")
    doc_type = session.scalar(select(DocumentType).where(DocumentType.key == document_type_key))
    if doc_type is None:
        raise UploadError(f"Unknown document type '{document_type_key}'. Please choose a type from the list.")

    file_type, text = extract_text(filename, data)  # raises ExtractionError with a friendly message

    document = Document(
        title=title.strip() or Path(filename).stem,
        document_type=doc_type,
        project_name=project_name.strip(),
        uploaded_by=uploaded_by,
    )
    version = DocumentVersion(
        version_number=1, original_filename=filename, file_type=file_type, extracted_text=text
    )
    document.versions.append(version)
    review = Review(document_version=version, rulebook_version=doc_type.latest_version, status="queued")
    session.add_all([document, review])
    session.commit()

    return UploadResult(
        document_id=document.id,
        version_id=version.id,
        version_number=version.version_number,
        review_id=review.id,
        review_status=review.status,
        file_type=file_type,
        extracted_characters=len(text),
        extracted_text_preview=text[:PREVIEW_CHARS],
    )


def get_document(session: Session, document_id: int) -> DocumentDetail | None:
    """A document with all its versions and their reviews, or None if it doesn't exist."""
    document = session.get(Document, document_id)
    if document is None:
        return None
    return DocumentDetail(
        id=document.id,
        title=document.title,
        document_type=document.document_type.key,
        project_name=document.project_name,
        uploaded_by=document.uploaded_by,
        created_at=document.created_at,
        versions=[
            VersionSummary(
                id=v.id,
                version_number=v.version_number,
                original_filename=v.original_filename,
                file_type=v.file_type,
                extracted_characters=len(v.extracted_text),
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
