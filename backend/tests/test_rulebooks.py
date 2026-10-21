import pytest

from app.config import settings
from app.services.rulebooks import RulebookError, parse_rulebook, rulebook_to_markdown

EXPECTED_RULE_COUNTS = {"brd": 10, "frd": 10, "process_as_is": 9, "process_to_be": 9, "roadmap": 10}

VALID = """---
doc_type: test_doc
display_name: Test Document
pass_threshold: 75
description: For tests.
---

Optional introduction text is fine here.

## TST-01: First rule
- weight: high
- critical: true
- check: The document has a title
  and a version number.
- pass_example: "Title v1.0"

## TST-02: Second rule
- weight: low
- check: The document lists what is out of scope.
"""


def errors_for(text):
    with pytest.raises(RulebookError) as info:
        parse_rulebook(text)
    return info.value.errors


# ---------- The shipped rulebooks ----------


@pytest.mark.parametrize("key, count", EXPECTED_RULE_COUNTS.items())
def test_shipped_rulebooks_are_valid(key, count):
    path = settings.rulebooks_dir / f"{key}.md"
    rulebook = parse_rulebook(path.read_text(encoding="utf-8"), source=path.name)
    assert rulebook.doc_type == key
    assert len(rulebook.rules) == count
    critical = [r for r in rulebook.rules if r.critical]
    assert 1 <= len(critical) <= 3, "each type should have 1 to 3 critical rules"
    assert all(r.pass_example and r.fail_example for r in rulebook.rules)


# ---------- Parsing ----------


def test_parses_valid_rulebook():
    rulebook = parse_rulebook(VALID)
    assert rulebook.doc_type == "test_doc"
    assert rulebook.pass_threshold == 75
    first, second = rulebook.rules
    assert first.id == "TST-01" and first.title == "First rule"
    assert first.weight == "high" and first.critical is True
    assert first.check == "The document has a title and a version number."  # joined across lines
    assert second.critical is False  # critical defaults to false
    assert second.pass_example is None


def test_export_then_import_gives_the_same_rulebook():
    rulebook = parse_rulebook(VALID)
    assert parse_rulebook(rulebook_to_markdown(rulebook, version=3)) == rulebook


def test_old_files_with_category_still_work():
    old = VALID.replace("- weight: high", "- category: Structure\n- weight: high")
    assert parse_rulebook(old) == parse_rulebook(VALID)


def test_windows_line_endings_are_fine():
    assert len(parse_rulebook(VALID.replace("\n", "\r\n")).rules) == 2


# ---------- Clear errors for broken rulebooks ----------


def test_missing_settings_block():
    assert "must start with a '---' line" in errors_for("## TST-01: Rule\n- weight: high")[0]


def test_unclosed_settings_block():
    assert "never closed" in errors_for("---\ndoc_type: x\n## TST-01: Rule")[0]


def test_bad_weight():
    errs = errors_for(VALID.replace("weight: high", "weight: 10"))
    assert errs == ["TST-01: weight must be high, medium or low (got '10')."]


def test_bad_critical():
    errs = errors_for(VALID.replace("critical: true", "critical: maybe"))
    assert errs == ["TST-01: critical must be true or false (got 'maybe')."]


def test_duplicate_rule_id():
    errs = errors_for(VALID.replace("TST-02", "TST-01"))
    assert any("TST-01 is used more than once" in e for e in errs)


def test_missing_check():
    errs = errors_for(VALID.replace("- check: The document lists what is out of scope.\n", ""))
    assert errs == ["TST-02: missing 'check'."]


def test_misspelled_field():
    errs = errors_for(VALID.replace("- weight: low", "- wieght: low"))
    assert "TST-02: unknown field 'wieght'" in errs[0]
    assert "TST-02: missing 'weight'." in errs


def test_bad_heading():
    errs = errors_for(VALID.replace("## TST-02: Second rule", "## Second rule"))
    assert "should look like '## BRD-01: Rule title'" in errs[0]


def test_no_rules():
    errs = errors_for(VALID.split("Optional introduction")[0])
    assert errs == ["No rules found. Each rule needs a heading like '## BRD-01: Rule title'."]


def test_missing_doc_type_and_bad_threshold():
    text = VALID.replace("doc_type: test_doc\n", "").replace("pass_threshold: 75", "pass_threshold: 150")
    errs = errors_for(text)
    assert any("Missing 'doc_type'" in e for e in errs)
    assert any("pass_threshold must be a whole number from 0 to 100" in e for e in errs)


def test_all_problems_reported_at_once():
    text = VALID.replace("weight: high", "weight: huge").replace("- check: The document lists what is out of scope.\n", "")
    assert len(errors_for(text)) == 2


# ---------- Database and API ----------


def test_list_document_types(client):
    response = client.get("/api/document-types")
    assert response.status_code == 200
    types = {t["key"]: t for t in response.json()}
    assert set(types) == set(EXPECTED_RULE_COUNTS)
    assert types["brd"]["rule_count"] == 10
    assert types["brd"]["version"] == 1


def test_get_document_type(client):
    body = client.get("/api/document-types/brd").json()
    assert body["display_name"] == "Business Requirements Document"
    assert body["updated_by"] == "system"
    assert [r["id"] for r in body["rules"] if r["critical"]] == ["BRD-03", "BRD-04"]


def test_unknown_document_type(client):
    response = client.get("/api/document-types/nope")
    assert response.status_code == 404
    assert "No document type called 'nope'" in response.json()["detail"]


def test_export_round_trips(client):
    response = client.get("/api/document-types/frd/export")
    assert response.status_code == 200
    assert 'filename="frd.md"' in response.headers["content-disposition"]
    rulebook = parse_rulebook(response.text)
    assert len(rulebook.rules) == 10


def test_loading_twice_does_not_duplicate(session):
    from app.services.rulebooks import list_document_types, load_builtin_rulebooks

    load_builtin_rulebooks(session, settings.rulebooks_dir)
    assert len(list_document_types(session)) == 5


def test_broken_file_is_skipped_others_still_load(session, tmp_path, caplog):
    from app.services.rulebooks import list_document_types, load_builtin_rulebooks

    (tmp_path / "good.md").write_text(VALID, encoding="utf-8")
    (tmp_path / "bad.md").write_text(VALID.replace("doc_type: test_doc", "doc_type: other").replace("weight: high", "weight: 10"), encoding="utf-8")
    load_builtin_rulebooks(session, tmp_path)
    keys = [t.key for t in list_document_types(session)]
    assert "test_doc" in keys and "other" not in keys
    assert "rulebooks/bad.md has 1 problem(s)" in caplog.text
