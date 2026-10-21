"""Rulebooks: read them from Markdown, check they're valid, store them, and write them back out.

Markdown format (see rulebooks/brd.md for a full example):

    ---
    doc_type: brd
    display_name: Business Requirements Document
    pass_threshold: 80
    description: One-line description.
    ---

    ## BRD-01: Rule title
    - weight: low            (high, medium or low)
    - critical: false        (true or false)
    - check: What the reviewer must check. Can continue on
      indented lines below.
    - pass_example: optional
    - fail_example: optional
"""

import logging
import re
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DocumentType, RulebookVersion
from app.schemas import DocumentTypeDetail, DocumentTypeSummary, Rule, Rulebook

logger = logging.getLogger(__name__)

FRONT_MATTER_FIELDS = {"doc_type", "display_name", "pass_threshold", "description", "version"}
RULE_FIELDS = {"weight", "critical", "check", "pass_example", "fail_example"}
REQUIRED_RULE_FIELDS = ["weight", "check"]
# Older rulebooks had a "category" field; it is no longer used, so it is quietly ignored.
IGNORED_RULE_FIELDS = {"category"}
WEIGHTS = {"high", "medium", "low"}

HEADING = re.compile(r"^##\s+([A-Za-z]+-\d+)\s*:\s*(.+?)\s*$")
FIELD = re.compile(r"^-\s*([A-Za-z_]+)\s*:\s*(.*)$")
DOC_TYPE_KEY = re.compile(r"^[a-z][a-z0-9_]*$")


class RulebookError(ValueError):
    """A rulebook is malformed. `errors` lists every problem found, in plain language."""

    def __init__(self, source: str, errors: list[str]):
        self.source = source
        self.errors = errors
        super().__init__(f"{source} has {len(errors)} problem(s):\n- " + "\n- ".join(errors))


# ---------- Reading Markdown ----------


def parse_rulebook(text: str, source: str = "Rulebook") -> Rulebook:
    """Turn rulebook Markdown into a Rulebook. Raises RulebookError listing every problem found."""
    errors: list[str] = []
    lines = text.replace("\r\n", "\n").split("\n")

    # 1. Front matter between the first two '---' lines.
    if not lines or lines[0].strip() != "---":
        raise RulebookError(source, ["The file must start with a '---' line, followed by the settings block (doc_type, display_name, ...)."])
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise RulebookError(source, ["The settings block at the top is never closed. Add a '---' line after it."])

    try:
        meta = yaml.safe_load("\n".join(lines[1:end])) or {}
    except yaml.YAMLError as e:
        raise RulebookError(source, [f"The settings block at the top couldn't be read: {e}"])
    if not isinstance(meta, dict):
        raise RulebookError(source, ["The settings block at the top must be 'name: value' lines."])

    for key in sorted(set(meta) - FRONT_MATTER_FIELDS):
        errors.append(f"Unknown setting '{key}'. Allowed: {', '.join(sorted(FRONT_MATTER_FIELDS))}.")
    doc_type = str(meta.get("doc_type", "")).strip()
    if not doc_type:
        errors.append("Missing 'doc_type' in the settings block (for example: doc_type: brd).")
    elif not DOC_TYPE_KEY.match(doc_type):
        errors.append(f"doc_type '{doc_type}' must be lowercase letters, numbers and underscores (for example: data_migration_plan).")
    display_name = str(meta.get("display_name", "")).strip()
    if not display_name:
        errors.append("Missing 'display_name' in the settings block.")
    pass_threshold = meta.get("pass_threshold", 80)
    if not isinstance(pass_threshold, int) or isinstance(pass_threshold, bool) or not 0 <= pass_threshold <= 100:
        errors.append(f"pass_threshold must be a whole number from 0 to 100 (got '{pass_threshold}').")
        pass_threshold = 80

    # 2. Rules: one '## ID: Title' heading each, followed by '- field: value' lines.
    raw_rules: list[dict] = []
    current: dict | None = None
    current_field: str | None = None
    for line_no, line in enumerate(lines[end + 1 :], start=end + 2):
        stripped = line.strip()
        if not stripped:
            continue
        if line.startswith("##"):
            match = HEADING.match(stripped)
            if not match:
                errors.append(f"Line {line_no}: heading '{stripped}' should look like '## BRD-01: Rule title'.")
                current, current_field = None, None
                continue
            current = {"id": match.group(1).upper(), "title": match.group(2), "fields": {}, "line": line_no}
            raw_rules.append(current)
            current_field = None
            continue
        if current is None:
            continue  # free text before the first rule is allowed (e.g. an introduction)
        field_match = FIELD.match(stripped)
        if field_match and not line[0].isspace():
            current_field = field_match.group(1).lower()
            if current_field in current["fields"]:
                errors.append(f"{current['id']}: '{current_field}' is listed twice.")
            current["fields"][current_field] = field_match.group(2).strip()
        elif line[0].isspace() and current_field:
            current["fields"][current_field] += " " + stripped  # continuation of the previous field
        else:
            errors.append(f"Line {line_no} ({current['id']}): expected '- field: value' but found '{stripped}'.")

    if not raw_rules:
        errors.append("No rules found. Each rule needs a heading like '## BRD-01: Rule title'.")

    rules: list[Rule] = []
    seen_ids: set[str] = set()
    for raw in raw_rules:
        rule_id, fields = raw["id"], raw["fields"]
        if rule_id in seen_ids:
            errors.append(f"Rule ID {rule_id} is used more than once. Each rule needs its own ID.")
        seen_ids.add(rule_id)
        for name in sorted(set(fields) - RULE_FIELDS - IGNORED_RULE_FIELDS):
            errors.append(f"{rule_id}: unknown field '{name}'. Allowed: {', '.join(sorted(RULE_FIELDS))}.")
        missing = [f for f in REQUIRED_RULE_FIELDS if not fields.get(f)]
        for name in missing:
            errors.append(f"{rule_id}: missing '{name}'.")
        weight = fields.get("weight", "").lower()
        if weight and weight not in WEIGHTS:
            errors.append(f"{rule_id}: weight must be high, medium or low (got '{fields['weight']}').")
        critical_text = fields.get("critical", "false").lower()
        if critical_text not in ("true", "false"):
            errors.append(f"{rule_id}: critical must be true or false (got '{fields['critical']}').")
        if missing or (weight and weight not in WEIGHTS) or critical_text not in ("true", "false"):
            continue
        rules.append(
            Rule(
                id=rule_id,
                title=raw["title"],
                weight=weight,
                critical=critical_text == "true",
                check=fields["check"],
                pass_example=fields.get("pass_example") or None,
                fail_example=fields.get("fail_example") or None,
            )
        )

    if errors:
        raise RulebookError(source, errors)
    return Rulebook(
        doc_type=doc_type,
        display_name=display_name,
        description=str(meta.get("description", "")).strip(),
        pass_threshold=pass_threshold,
        rules=rules,
    )


# ---------- Writing Markdown ----------


def rulebook_to_markdown(rulebook: Rulebook, version: int | None = None) -> str:
    """Turn a Rulebook back into Markdown, in the same format parse_rulebook reads."""
    meta = {
        "doc_type": rulebook.doc_type,
        "display_name": rulebook.display_name,
        "pass_threshold": rulebook.pass_threshold,
        "description": rulebook.description,
    }
    if version is not None:
        meta["version"] = version
    out = ["---", yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).strip(), "---", ""]
    for rule in rulebook.rules:
        out.append(f"## {rule.id}: {rule.title}")
        out.append(f"- weight: {rule.weight}")
        out.append(f"- critical: {'true' if rule.critical else 'false'}")
        out.append(f"- check: {rule.check}")
        if rule.pass_example:
            out.append(f"- pass_example: {rule.pass_example}")
        if rule.fail_example:
            out.append(f"- fail_example: {rule.fail_example}")
        out.append("")
    return "\n".join(out)


# ---------- Database ----------


def load_builtin_rulebooks(session: Session, folder: Path) -> None:
    """On startup, add any rulebook file in `folder` whose type isn't in the database yet.

    Once a type is in the database, the database is the source of truth: later edits to the
    file are NOT picked up automatically (they're made in the app, or by uploading the file).
    A broken file is skipped with a clear error in the server log; the rest still load.
    """
    for path in sorted(folder.glob("*.md")):
        try:
            rulebook = parse_rulebook(path.read_text(encoding="utf-8"), source=f"rulebooks/{path.name}")
        except RulebookError as e:
            logger.error("Skipped a rulebook that has problems. %s", e)
            continue
        exists = session.scalar(select(DocumentType).where(DocumentType.key == rulebook.doc_type))
        if exists:
            continue
        doc_type = DocumentType(
            key=rulebook.doc_type,
            display_name=rulebook.display_name,
            description=rulebook.description,
            is_builtin=True,
        )
        doc_type.versions.append(
            RulebookVersion(
                version_number=1,
                pass_threshold=rulebook.pass_threshold,
                rules_json=[rule.model_dump() for rule in rulebook.rules],
                changed_by="system",
                change_note=f"Loaded from rulebooks/{path.name}",
            )
        )
        session.add(doc_type)
        logger.info("Loaded rulebook %s from %s", rulebook.doc_type, path.name)
    session.commit()


def _summary(doc_type: DocumentType) -> DocumentTypeSummary:
    latest = doc_type.latest_version
    return DocumentTypeSummary(
        key=doc_type.key,
        display_name=doc_type.display_name,
        description=doc_type.description,
        is_builtin=doc_type.is_builtin,
        version=latest.version_number,
        rule_count=len(latest.rules_json),
    )


def list_document_types(session: Session) -> list[DocumentTypeSummary]:
    """All document types shown in the type picker: built-in first, then custom, by name."""
    rows = session.scalars(
        select(DocumentType)
        .where(DocumentType.is_listed)
        .order_by(DocumentType.is_builtin.desc(), DocumentType.id)
    )
    return [_summary(doc_type) for doc_type in rows]


def get_document_type(session: Session, key: str) -> DocumentTypeDetail | None:
    """One document type with its latest rules, or None if the key doesn't exist."""
    doc_type = session.scalar(select(DocumentType).where(DocumentType.key == key))
    if doc_type is None:
        return None
    latest = doc_type.latest_version
    return DocumentTypeDetail(
        **_summary(doc_type).model_dump(),
        pass_threshold=latest.pass_threshold,
        updated_by=latest.changed_by,
        updated_at=latest.created_at,
        rules=[Rule(**rule) for rule in latest.rules_json],
    )


def export_rulebook_markdown(session: Session, key: str) -> str | None:
    """The latest rulebook for a type as Markdown, or None if the key doesn't exist."""
    detail = get_document_type(session, key)
    if detail is None:
        return None
    rulebook = Rulebook(
        doc_type=detail.key,
        display_name=detail.display_name,
        description=detail.description,
        pass_threshold=detail.pass_threshold,
        rules=detail.rules,
    )
    return rulebook_to_markdown(rulebook, version=detail.version)
