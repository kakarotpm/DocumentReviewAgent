"""API endpoints for document types and their rulebooks."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import DocumentTypeDetail, DocumentTypeSummary
from app.services import rulebooks

router = APIRouter(prefix="/api/document-types", tags=["Document types"])


def _not_found(key: str):
    return HTTPException(404, f"No document type called '{key}'. Use GET /api/document-types to see the available types.")


@router.get("", response_model=list[DocumentTypeSummary])
def list_document_types(session: Session = Depends(get_session)):
    """All document types available for review."""
    return rulebooks.list_document_types(session)


@router.get("/{key}", response_model=DocumentTypeDetail)
def get_document_type(key: str, session: Session = Depends(get_session)):
    """One document type with its current rules."""
    detail = rulebooks.get_document_type(session, key)
    if detail is None:
        raise _not_found(key)
    return detail


@router.get("/{key}/export", response_class=PlainTextResponse)
def export_document_type(key: str, session: Session = Depends(get_session)):
    """Download the current rulebook as a Markdown file."""
    markdown = rulebooks.export_rulebook_markdown(session, key)
    if markdown is None:
        raise _not_found(key)
    return PlainTextResponse(
        markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{key}.md"'},
    )
