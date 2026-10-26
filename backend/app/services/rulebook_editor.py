"""Changing rulebooks: create document types, save new versions, and preview changes.

Three ways in, all ending in the same save:
  1. Manual edits in the UI        -> save_rulebook / create_document_type
  2. Uploading a .md rulebook      -> preview_markdown, then save
  3. Describing changes in a prompt -> preview_prompt (AI drafts), then save
Previews never save anything; the user confirms first.
"""

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DocumentType, RulebookVersion
from app.schemas import (
    DocumentTypeDetail,
    DraftRuleRequest,
    DraftRuleResult,
    PromptRulesRequest,
    Rule,
    RuleChange,
    RuleDiff,
    Rulebook,
    RulebookPreview,
    RulebookVersionInfo,
    SaveRulebookRequest,
)
from app.services import llm
from app.services.rulebooks import DOC_TYPE_KEY, RulebookError, get_document_type, parse_rulebook

RULE_ID = re.compile(r"^[A-Z]+(?:-[A-Z]+)*-\d+$")  # BRD-01, FRD-XL-01
RULE_FIELDS = ["title", "part", "weight", "critical", "check", "pass_example", "fail_example"]


class EditError(ValueError):
    """A change can't be saved. `errors` lists each problem in plain language."""

    def __init__(self, message: str, errors: list[str] | None = None):
        self.message = message
        self.errors = errors or []
        super().__init__(message)


# ---------- Helpers ----------


def key_from_name(display_name: str) -> str:
    """'Data Migration Plan' -> 'data_migration_plan'."""
    return re.sub(r"[^a-z0-9]+", "_", display_name.lower()).strip("_") or "custom"


def id_prefix(display_name: str) -> str:
    """'Data Migration Plan' -> 'DMP'. Used for new rule IDs like DMP-01."""
    words = re.findall(r"[A-Za-z]+", display_name)
    return "".join(w[0] for w in words).upper()[:4] or "CUS"


def _next_ids(prefix: str, existing: set[str], count: int) -> list[str]:
    """The next free IDs after the prefix: FRD -> FRD-11, FRD-XL -> FRD-XL-05."""
    numbers = [int(i[len(prefix) + 1:]) for i in existing if i.startswith(prefix + "-") and i[len(prefix) + 1:].isdigit()]
    start = max(numbers, default=0) + 1
    return [f"{prefix}-{n:02d}" for n in range(start, start + count)]


def validate_rulebook(rulebook: Rulebook) -> list[str]:
    """Problems with a rulebook coming from the editor (the .md parser has its own checks)."""
    errors = []
    if not DOC_TYPE_KEY.match(rulebook.doc_type):
        errors.append("The type key must be lowercase letters, numbers and underscores.")
    if not rulebook.display_name.strip():
        errors.append("Please give the document type a name.")
    if not 0 <= rulebook.pass_threshold <= 100:
        errors.append("The pass threshold must be between 0 and 100.")
    if not rulebook.rules:
        errors.append("Add at least one rule.")
    seen = set()
    for number, rule in enumerate(rulebook.rules, start=1):
        label = rule.id or f"Rule {number}"
        if not RULE_ID.match(rule.id):
            errors.append(f"{label}: the rule ID should look like BRD-01.")
        if rule.id in seen:
            errors.append(f"{label}: this rule ID is used more than once.")
        seen.add(rule.id)
        for field in ("title", "check"):
            if not getattr(rule, field).strip():
                errors.append(f"{label}: please fill in the {field}.")
    return errors


def diff_rulebooks(old: Rulebook, new: Rulebook) -> RuleDiff:
    """What's different between two rulebooks, rule by rule (matched on rule ID)."""
    old_rules = {r.id: r for r in old.rules}
    new_rules = {r.id: r for r in new.rules}
    changed = []
    for rule_id, after in new_rules.items():
        before = old_rules.get(rule_id)
        if before is None:
            continue
        fields = [f for f in RULE_FIELDS if getattr(before, f) != getattr(after, f)]
        if fields:
            changed.append(RuleChange(rule_id=rule_id, before=before, after=after, changed_fields=fields))
    return RuleDiff(
        added=[r for i, r in new_rules.items() if i not in old_rules],
        removed=[r for i, r in old_rules.items() if i not in new_rules],
        changed=changed,
        settings_changed=[f for f in ("display_name", "description", "pass_threshold") if getattr(old, f) != getattr(new, f)],
    )


def is_empty_diff(diff: RuleDiff) -> bool:
    return not (diff.added or diff.removed or diff.changed or diff.settings_changed)


def current_rulebook(session: Session, key: str) -> Rulebook | None:
    detail = get_document_type(session, key)
    if detail is None:
        return None
    return Rulebook(
        doc_type=detail.key,
        display_name=detail.display_name,
        description=detail.description,
        pass_threshold=detail.pass_threshold,
        rules=detail.rules,
    )


def _find_type(session: Session, key: str) -> DocumentType | None:
    return session.scalar(select(DocumentType).where(DocumentType.key == key))


# ---------- Saving ----------


def create_document_type(session: Session, request: SaveRulebookRequest) -> DocumentTypeDetail:
    """Create a new document type with version 1 of its rulebook."""
    rulebook = request.rulebook
    changed_by = request.changed_by.strip()
    errors = validate_rulebook(rulebook) + ([] if changed_by else ["Please enter your name."])
    if errors:
        raise EditError("The new document type can't be saved yet.", errors)
    if _find_type(session, rulebook.doc_type):
        raise EditError(
            f"A document type called '{rulebook.doc_type}' already exists. Choose a different name, or open that type to change it."
        )
    doc_type = DocumentType(
        key=rulebook.doc_type,
        display_name=rulebook.display_name.strip(),
        description=rulebook.description.strip(),
        is_builtin=False,
        is_listed=request.listed,
    )
    doc_type.versions.append(
        RulebookVersion(
            version_number=1,
            pass_threshold=rulebook.pass_threshold,
            rules_json=[r.model_dump() for r in rulebook.rules],
            changed_by=changed_by,
            change_note=request.change_note.strip() or "Created",
        )
    )
    session.add(doc_type)
    session.commit()
    return get_document_type(session, doc_type.key)


def save_rulebook(session: Session, key: str, request: SaveRulebookRequest) -> DocumentTypeDetail | None:
    """Save a new version of an existing rulebook. Returns None if the type doesn't exist."""
    doc_type = _find_type(session, key)
    if doc_type is None:
        return None
    rulebook = request.rulebook.model_copy(update={"doc_type": key})
    changed_by = request.changed_by.strip()
    errors = validate_rulebook(rulebook) + ([] if changed_by else ["Please enter your name."])
    if errors:
        raise EditError("These changes can't be saved yet.", errors)
    if is_empty_diff(diff_rulebooks(current_rulebook(session, key), rulebook)):
        raise EditError("Nothing has changed, so there's nothing to save.")

    doc_type.display_name = rulebook.display_name.strip()
    doc_type.description = rulebook.description.strip()
    doc_type.versions.append(
        RulebookVersion(
            version_number=doc_type.latest_version.version_number + 1,
            pass_threshold=rulebook.pass_threshold,
            rules_json=[r.model_dump() for r in rulebook.rules],
            changed_by=changed_by,
            change_note=request.change_note.strip(),
        )
    )
    session.commit()
    return get_document_type(session, key)


def list_versions(session: Session, key: str) -> list[RulebookVersionInfo] | None:
    doc_type = _find_type(session, key)
    if doc_type is None:
        return None
    return [
        RulebookVersionInfo(
            version=v.version_number,
            changed_by=v.changed_by,
            change_note=v.change_note,
            created_at=v.created_at,
            rule_count=len(v.rules_json),
        )
        for v in reversed(doc_type.versions)
    ]


# ---------- Previews (nothing is saved) ----------


def _preview(session: Session, rulebook: Rulebook, summary: str) -> RulebookPreview:
    existing = current_rulebook(session, rulebook.doc_type)
    if existing is None:
        return RulebookPreview(mode="new", rulebook=rulebook, diff=None, summary=summary)
    return RulebookPreview(mode="update", rulebook=rulebook, diff=diff_rulebooks(existing, rulebook), summary=summary)


def preview_markdown(session: Session, text: str, filename: str, target_key: str | None) -> RulebookPreview:
    """Check an uploaded .md rulebook and show what saving it would change.

    With `target_key`, the file updates that type whatever doc_type it says inside.
    Otherwise it updates the type named in the file, or creates it if it's new.
    """
    try:
        rulebook = parse_rulebook(text, source=filename)
    except RulebookError as e:
        raise EditError(f"'{filename}' has problems that need fixing before it can be used.", e.errors)
    if target_key:
        if _find_type(session, target_key) is None:
            raise EditError(f"No document type called '{target_key}'.")
        rulebook = rulebook.model_copy(update={"doc_type": target_key})
    return _preview(session, rulebook, f"Read {len(rulebook.rules)} rules from {filename}.")


def preview_prompt(session: Session, request: PromptRulesRequest) -> RulebookPreview:
    """Ask the AI to draft every rule for a NEW document type, and show the result."""
    instruction = request.instruction.strip()
    name = request.display_name.strip()
    if not name:
        raise EditError("Please give the new document type a name.")
    if not instruction:
        raise EditError("Please describe what a good document of this type must contain.")
    key = key_from_name(name)
    if _find_type(session, key):
        raise EditError(f"A document type called '{name}' already exists. Choose a different name, or open it to change it.")

    try:
        proposal = llm.draft_rules(instruction, name)
    except llm.AIError as e:
        raise EditError(str(e))

    ids = _next_ids(id_prefix(name), set(), len(proposal.rules))
    rules = [
        Rule(id=rule_id, title=p.title, weight=p.weight, critical=p.critical, check=p.check,
             pass_example=p.pass_example, fail_example=p.fail_example)
        for rule_id, p in zip(ids, proposal.rules)
    ]
    rulebook = Rulebook(doc_type=key, display_name=name, description=proposal.description, pass_threshold=80, rules=rules)
    return _preview(session, rulebook, proposal.summary)


def draft_rule(session: Session, key: str, request: DraftRuleRequest) -> DraftRuleResult:
    """Ask the AI to write one new rule, or change one existing rule. Nothing is saved:
    the user reviews the draft, can edit it, and then saves the rulebook as usual."""
    rulebook = current_rulebook(session, key)
    if rulebook is None:
        raise EditError(f"No document type called '{key}'.")
    instruction = request.instruction.strip()
    if not instruction:
        raise EditError("Please describe the rule, or the change you want.")
    original = None
    if request.rule_id:
        original = next((r for r in rulebook.rules if r.id == request.rule_id), None)
        if original is None:
            raise EditError(f"There's no rule {request.rule_id} in this rulebook. It may have been deleted.")

    part = original.part if original else request.part
    try:
        proposal = llm.draft_rule(instruction, rulebook, original, part)
    except llm.AIError as e:
        raise EditError(str(e))

    if original:
        rule_id = original.id
    else:
        prefix = rulebook.rules[0].id.split("-")[0] if rulebook.rules else id_prefix(rulebook.display_name)
        if part == "excel":
            prefix += "-XL"  # Excel rules are numbered separately: FRD-XL-01
        rule_id = _next_ids(prefix, {r.id for r in rulebook.rules}, 1)[0]
    rule = Rule(id=rule_id, title=proposal.title, part=part, weight=proposal.weight, critical=proposal.critical,
                check=proposal.check, pass_example=proposal.pass_example, fail_example=proposal.fail_example)
    return DraftRuleResult(rule=rule, summary=proposal.summary, original=original)
