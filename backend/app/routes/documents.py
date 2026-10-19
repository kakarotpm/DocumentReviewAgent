"""API endpoints for uploading and viewing documents."""

from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.db import get_session, get_session_factory
from app.schemas import DocumentDetail, DocumentListItem, UploadResult
from app.services import documents
from app.services.documents import UploadError
from app.services.extraction import ExtractionError
from app.services.review_engine import run_review

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("", response_model=UploadResult, status_code=201)
async def upload_document(
    background: BackgroundTasks,
    file: UploadFile = File(..., description="A .docx, .pdf, .md or .txt file, up to 10 MB"),
    document_type: str = Form(..., description="Document type key, e.g. brd"),
    uploaded_by: str = Form(..., description="Your name"),
    title: str = Form("", description="Leave blank to use the file name"),
    project_name: str = Form(""),
    session: Session = Depends(get_session),
    session_factory=Depends(get_session_factory),
):
    """Upload a document: its text is extracted, Version 1 is created, and the review starts."""
    data = await file.read()  # held in memory only; never saved to disk
    try:
        result = documents.create_document(
            session,
            filename=file.filename or "upload",
            data=data,
            document_type_key=document_type,
            uploaded_by=uploaded_by,
            title=title,
            project_name=project_name,
        )
    except (UploadError, ExtractionError) as e:
        raise HTTPException(400, str(e))
    background.add_task(run_review, result.review_id, session_factory)
    return result


@router.post("/{document_id}/versions", response_model=UploadResult, status_code=201)
async def upload_revised_version(
    document_id: int,
    background: BackgroundTasks,
    file: UploadFile = File(..., description="The revised document"),
    session: Session = Depends(get_session),
    session_factory=Depends(get_session_factory),
):
    """Upload a revised version of a document; it's reviewed against the latest rulebook."""
    data = await file.read()
    try:
        result = documents.add_version(session, document_id=document_id, filename=file.filename or "upload", data=data)
    except ExtractionError as e:
        raise HTTPException(400, str(e))
    if result is None:
        raise HTTPException(404, f"No document with ID {document_id}.")
    background.add_task(run_review, result.review_id, session_factory)
    return result


@router.get("", response_model=list[DocumentListItem])
def list_documents(
    search: str = "",
    document_type: str = "",
    status: str = Query("", description="Passed, Failed, Corrected, In review or Error"),
    project: str = "",
    date_from: date | None = None,
    date_to: date | None = None,
    sort: str = Query("updated", description="title, type, project, uploaded_by, score, status, versions or updated"),
    descending: bool = True,
    session: Session = Depends(get_session),
):
    """All documents, with search, filters and sorting."""
    return documents.list_documents(
        session,
        search=search,
        document_type=document_type,
        status=status,
        project=project,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        descending=descending,
    )


@router.get("/projects", response_model=list[str])
def list_projects(session: Session = Depends(get_session)):
    """Project names in use, for filter dropdowns."""
    return documents.list_projects(session)


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(document_id: int, session: Session = Depends(get_session)):
    """A document with its versions and their reviews."""
    detail = documents.get_document(session, document_id)
    if detail is None:
        raise HTTPException(404, f"No document with ID {document_id}.")
    return detail
