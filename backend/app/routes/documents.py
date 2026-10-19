"""API endpoints for uploading and viewing documents."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import DocumentDetail, UploadResult
from app.services import documents
from app.services.documents import UploadError
from app.services.extraction import ExtractionError

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("", response_model=UploadResult, status_code=201)
async def upload_document(
    file: UploadFile = File(..., description="A .docx, .pdf, .md or .txt file, up to 10 MB"),
    document_type: str = Form(..., description="Document type key, e.g. brd"),
    uploaded_by: str = Form(..., description="Your name"),
    title: str = Form("", description="Leave blank to use the file name"),
    project_name: str = Form(""),
    session: Session = Depends(get_session),
):
    """Upload a document: its text is extracted, and Version 1 and a review are created."""
    data = await file.read()  # held in memory only; never saved to disk
    try:
        return documents.create_document(
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


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(document_id: int, session: Session = Depends(get_session)):
    """A document with its versions and their reviews."""
    detail = documents.get_document(session, document_id)
    if detail is None:
        raise HTTPException(404, f"No document with ID {document_id}.")
    return detail
