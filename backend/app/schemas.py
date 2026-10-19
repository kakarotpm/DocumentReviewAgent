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
    document_type_name: str
    project_name: str
    uploaded_by: str
    status: str
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


# ---------- What the AI must return (validated with these models) ----------

ReviewStatus = Literal["met", "partially_met", "not_met"]


class AISuggestion(BaseModel):
    type: Literal["add", "change", "delete"]
    location: str
    current_text: str | None = None
    proposed_text: str | None = None
    rationale: str


class AIRuleJudgement(BaseModel):
    rule_id: str
    status: ReviewStatus
    evidence: str
    location: str
    explanation: str
    suggestions: list[AISuggestion]


class AIReviewOutput(BaseModel):
    results: list[AIRuleJudgement]


class AIProposedRule(BaseModel):
    id: str | None = None
    title: str
    category: str
    weight: Weight
    critical: bool
    check: str
    pass_example: str | None = None
    fail_example: str | None = None


class AIProposedRulebook(BaseModel):
    display_name: str
    description: str
    summary: str
    rules: list[AIProposedRule]


# ---------- Reviews ----------


class SuggestionOut(BaseModel):
    id: int
    type: str
    location: str
    current_text: str | None
    proposed_text: str | None
    rationale: str
    user_state: str


class RuleResultOut(BaseModel):
    rule_id: str
    title: str
    category: str
    weight: str
    critical: bool
    status: str
    points_earned: float
    points_possible: int
    evidence: str
    location: str
    explanation: str
    suggestions: list[SuggestionOut]


class CategoryOut(BaseModel):
    category: str
    points_earned: float
    points_possible: int


class RuleRef(BaseModel):
    rule_id: str
    title: str


class VersionComparison(BaseModel):
    previous_version_number: int
    previous_review_id: int
    previous_score: int
    score_change: int
    rules_updated: bool  # the rulebook changed between the two reviews
    newly_met: list[RuleRef]
    newly_not_met: list[RuleRef]


class ReviewDetail(BaseModel):
    id: int
    status: str
    error_message: str | None
    is_demo: bool
    score: int | None
    passed: bool | None
    pass_threshold: int
    critical_failures: list[RuleRef]
    model_name: str | None
    prompt_version: str | None
    rulebook_version: int
    rule_count: int
    created_at: datetime
    completed_at: datetime | None
    document_id: int
    document_title: str
    document_type_key: str
    document_type_name: str
    project_name: str
    uploaded_by: str
    version_number: int
    latest_version_number: int
    original_filename: str
    categories: list[CategoryOut]
    rules: list[RuleResultOut]
    comparison: VersionComparison | None


class SuggestionStateUpdate(BaseModel):
    user_state: Literal["open", "done", "dismissed"]


# ---------- Documents list ----------


class DocumentListItem(BaseModel):
    id: int
    title: str
    document_type_key: str
    document_type_name: str
    project_name: str
    uploaded_by: str
    latest_score: int | None
    latest_review_id: int | None
    status: str  # Passed / Failed / Corrected / In review / Error
    versions: int
    updated_at: datetime


# ---------- Rulebook editing ----------


class RuleChange(BaseModel):
    rule_id: str
    before: Rule
    after: Rule
    changed_fields: list[str]


class RuleDiff(BaseModel):
    added: list[Rule]
    removed: list[Rule]
    changed: list[RuleChange]
    settings_changed: list[str]  # display_name / description / pass_threshold


class RulebookPreview(BaseModel):
    mode: Literal["new", "update"]
    rulebook: Rulebook
    diff: RuleDiff | None  # None for a brand-new type
    summary: str


class SaveRulebookRequest(BaseModel):
    rulebook: Rulebook
    changed_by: str
    change_note: str = ""
    listed: bool = True  # only used when creating: False = one-off custom type, hidden from pickers


class PromptRulesRequest(BaseModel):
    instruction: str
    target_key: str | None = None  # change this existing type; None = create a new type
    display_name: str | None = None  # name for a new type


class RulebookVersionInfo(BaseModel):
    version: int
    changed_by: str
    change_note: str
    created_at: datetime
    rule_count: int
