"""API endpoints for document types and their rulebooks."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import (
    DocumentTypeDetail,
    DocumentTypeSummary,
    PromptRulesRequest,
    RulebookPreview,
    RulebookVersionInfo,
    SaveRulebookRequest,
)
from app.services import rulebook_editor, rulebooks
from app.services.rulebook_editor import EditError

router = APIRouter(prefix="/api/document-types", tags=["Document types and rulebooks"])


def _not_found(key: str):
    return HTTPException(404, f"No document type called '{key}'. Use GET /api/document-types to see the available types.")


def _bad_request(e: EditError):
    return HTTPException(400, {"message": e.message, "errors": e.errors})


@router.get("", response_model=list[DocumentTypeSummary])
def list_document_types(session: Session = Depends(get_session)):
    """All document types available for review."""
    return rulebooks.list_document_types(session)


@router.post("", response_model=DocumentTypeDetail, status_code=201)
def create_document_type(request: SaveRulebookRequest, session: Session = Depends(get_session)):
    """Create a new document type with its rules."""
    try:
        return rulebook_editor.create_document_type(session, request)
    except EditError as e:
        raise _bad_request(e)


@router.post("/import-preview", response_model=RulebookPreview)
async def preview_markdown_upload(
    file: UploadFile = File(..., description="A rulebook .md file"),
    target_key: str = Form("", description="Leave blank to use the doc_type inside the file"),
    session: Session = Depends(get_session),
):
    """Check an uploaded .md rulebook and show what would change. Nothing is saved."""
    name = file.filename or "rulebook.md"
    if not name.lower().endswith(".md"):
        raise HTTPException(400, {"message": f"'{name}' isn't a .md file. Rulebooks are uploaded as Markdown (.md) files.", "errors": []})
    data = await file.read()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("cp1252", errors="replace")
    try:
        return rulebook_editor.preview_markdown(session, text, name, target_key or None)
    except EditError as e:
        raise _bad_request(e)


@router.post("/prompt-preview", response_model=RulebookPreview)
def preview_prompt(request: PromptRulesRequest, session: Session = Depends(get_session)):
    """Ask the AI to draft a new type or change an existing one. Nothing is saved."""
    try:
        return rulebook_editor.preview_prompt(session, request)
    except EditError as e:
        raise _bad_request(e)


@router.get("/{key}", response_model=DocumentTypeDetail)
def get_document_type(key: str, session: Session = Depends(get_session)):
    """One document type with its current rules."""
    detail = rulebooks.get_document_type(session, key)
    if detail is None:
        raise _not_found(key)
    return detail


@router.put("/{key}", response_model=DocumentTypeDetail)
def save_rulebook(key: str, request: SaveRulebookRequest, session: Session = Depends(get_session)):
    """Save changed rules as a new rulebook version."""
    try:
        detail = rulebook_editor.save_rulebook(session, key, request)
    except EditError as e:
        raise _bad_request(e)
    if detail is None:
        raise _not_found(key)
    return detail


@router.get("/{key}/versions", response_model=list[RulebookVersionInfo])
def list_versions(key: str, session: Session = Depends(get_session)):
    """Version history: who changed the rulebook, when, and why. Newest first."""
    versions = rulebook_editor.list_versions(session, key)
    if versions is None:
        raise _not_found(key)
    return versions


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
