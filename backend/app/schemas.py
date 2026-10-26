"""Data shapes shared by the services and the API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Weight = Literal["high", "medium", "low"]
Part = Literal["document", "excel"]  # Part A rules check the document; Part B rules check an Excel workbook


class Rule(BaseModel):
    id: str
    title: str
    part: Part = "document"
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
    has_excel_rules: bool = False  # true when the rulebook has a Part B (an Excel workbook can be added)
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
    workbook_filename: str | None = None  # the Excel workbook reviewed with this version, if any
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
    workbook_filename: str | None = None


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
    weight: Weight
    critical: bool
    check: str
    pass_example: str | None = None
    fail_example: str | None = None


class AIProposedSingleRule(BaseModel):
    title: str
    weight: Weight
    critical: bool
    check: str
    pass_example: str | None = None
    fail_example: str | None = None
    summary: str


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
    part: Part = "document"
    weight: str
    critical: bool
    status: str
    points_earned: float
    points_possible: int
    evidence: str
    location: str
    explanation: str
    suggestions: list[SuggestionOut]


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
    rule_count: int  # rules in this review (Part B rules only count when a workbook was uploaded)
    created_at: datetime
    completed_at: datetime | None
    # Excel workbook (Part B). Subtotals are None for a part that wasn't reviewed (or before the review is complete).
    workbook_filename: str | None = None
    document_subtotal: int | None = None
    excel_subtotal: int | None = None
    excel_rules_left_out: int = 0  # Part B rules not reviewed because no workbook was uploaded
    document_id: int
    document_title: str
    document_type_key: str
    document_type_name: str
    project_name: str
    uploaded_by: str
    version_number: int
    latest_version_number: int
    original_filename: str
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
    """Describe a NEW document type; the AI drafts all its rules."""

    instruction: str
    display_name: str


class DraftRuleRequest(BaseModel):
    """Describe one new rule, or (with rule_id) how to change an existing rule."""

    instruction: str
    rule_id: str | None = None


class DraftRuleResult(BaseModel):
    rule: Rule
    summary: str
    original: Rule | None  # the rule before the change; None for a new rule


class RulebookVersionInfo(BaseModel):
    version: int
    changed_by: str
    change_note: str
    created_at: datetime
    rule_count: int
