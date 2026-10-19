"""Data shapes shared by the services and the API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Weight = Literal["high", "medium", "low"]


class Rule(BaseModel):
    id: str
    title: str
    category: str
    weight: Weight
    critical: bool = False
    check: str
    pass_example: str | None = None
    fail_example: str | None = None


class Rulebook(BaseModel):
    doc_type: str
    display_name: str
    description: str = ""
    pass_threshold: int = 80
    rules: list[Rule]


class DocumentTypeSummary(BaseModel):
    key: str
    display_name: str
    description: str
    is_builtin: bool
    version: int
    rule_count: int


class DocumentTypeDetail(DocumentTypeSummary):
    pass_threshold: int
    updated_by: str
    updated_at: datetime
    rules: list[Rule]


class ReviewSummary(BaseModel):
    id: int
    status: str
    score: int | None
    passed: bool | None
    rulebook_version: int
    created_at: datetime


class VersionSummary(BaseModel):
    id: int
    version_number: int
    original_filename: str
    file_type: str
    extracted_characters: int
    uploaded_at: datetime
    reviews: list[ReviewSummary]


class DocumentDetail(BaseModel):
    id: int
    title: str
    document_type: str
    project_name: str
    uploaded_by: str
    created_at: datetime
    versions: list[VersionSummary]


class UploadResult(BaseModel):
    document_id: int
    version_id: int
    version_number: int
    review_id: int
    review_status: str
    file_type: str
    extracted_characters: int
    extracted_text_preview: str
