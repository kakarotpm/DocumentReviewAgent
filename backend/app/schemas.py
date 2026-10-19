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
