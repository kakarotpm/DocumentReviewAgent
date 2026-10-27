from types import SimpleNamespace

import pytest

from app.config import settings
from app.schemas import AIProposedRule, AIProposedRulebook, AIProposedSingleRule
from app.services import llm
from app.services.rulebook_editor import id_prefix, key_from_name

NEW_TYPE = {
    "doc_type": "data_migration_plan",
    "display_name": "Data Migration Plan",
    "description": "How data moves to the new system.",
    "pass_threshold": 75,
    "rules": [
        {"id": "DMP-01", "title": "Source to target mapping", "weight": "high", "critical": True, "check": "Every field is mapped."},
        {"id": "DMP-02", "title": "Rollback plan", "weight": "medium", "critical": False, "check": "A rollback plan exists."},
    ],
}


def create(client, rulebook=NEW_TYPE, **extra):
    return client.post("/api/document-types", json={"rulebook": rulebook, "changed_by": "Lead", **extra})


def brd(client):
    return client.get("/api/document-types/brd").json()


def save_brd(client, body, name="Lead", note=""):
    rulebook = {k: body[k] for k in ("display_name", "description", "pass_threshold", "rules")}
    return client.put("/api/document-types/brd", json={"rulebook": {**rulebook, "doc_type": "brd"}, "changed_by": name, "change_note": note})


def test_helpers():
    assert key_from_name("Data Migration Plan") == "data_migration_plan"
    assert id_prefix("Data Migration Plan") == "DMP"


# ---------- Manual: create a type, edit rules ----------


def test_create_new_document_type(client):
    response = create(client)
    assert response.status_code == 201, response.text
    assert response.json()["version"] == 1
    keys = [t["key"] for t in client.get("/api/document-types").json()]
    assert "data_migration_plan" in keys


def test_hidden_custom_type_is_not_listed_but_still_usable(client):
    assert create(client, listed=False).status_code == 201
    assert "data_migration_plan" not in [t["key"] for t in client.get("/api/document-types").json()]
    assert client.get("/api/document-types/data_migration_plan").status_code == 200


def test_duplicate_type_is_rejected(client):
    create(client)
    response = create(client)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]["message"]


def test_invalid_new_type_lists_problems(client):
    bad = {**NEW_TYPE, "display_name": " ", "rules": [{**NEW_TYPE["rules"][0], "id": "x1", "check": " "}]}
    errors = create(client, bad).json()["detail"]["errors"]
    assert "Please give the document type a name." in errors
    assert "x1: the rule ID should look like BRD-01." in errors
    assert "x1: please fill in the check." in errors


def test_edit_weight_and_critical_creates_new_version(client):
    body = brd(client)
    body["rules"][8]["weight"] = "high"  # BRD-09 risks
    body["rules"][8]["critical"] = True
    response = save_brd(client, body, note="Risks matter more")
    assert response.status_code == 200, response.text
    assert response.json()["version"] == 2
    assert response.json()["rules"][8]["critical"] is True
    history = client.get("/api/document-types/brd/versions").json()
    assert history[0] == {**history[0], "version": 2, "changed_by": "Lead", "change_note": "Risks matter more"}
    assert history[1]["changed_by"] == "system"


def test_add_and_delete_rules(client):
    body = brd(client)
    body["rules"].append({"id": "BRD-11", "title": "Glossary", "weight": "low", "critical": False, "check": "Terms are defined."})
    body["rules"] = [r for r in body["rules"] if r["id"] != "BRD-09"]
    detail = save_brd(client, body).json()
    assert [r["id"] for r in detail["rules"]][-2:] == ["BRD-10", "BRD-11"]
    assert "BRD-09" not in [r["id"] for r in detail["rules"]]


def test_saving_without_changes_is_rejected(client):
    response = save_brd(client, brd(client))
    assert response.status_code == 400
    assert "Nothing has changed" in response.json()["detail"]["message"]


def test_saving_needs_a_name(client):
    body = brd(client)
    body["pass_threshold"] = 70
    assert "Please enter your name." in save_brd(client, body, name=" ").json()["detail"]["errors"]


def test_past_reviews_keep_their_rules(client):
    from tests.test_reviews import upload

    review_id = upload(client)["review_id"]
    body = brd(client)
    body["rules"] = body["rules"][:3]
    save_brd(client, body)
    old = client.get(f"/api/reviews/{review_id}").json()
    assert old["rulebook_version"] == 1
    assert len(old["rules"]) == 10


# ---------- Upload a .md file ----------


def md_upload(client, text, target_key="", name="rules.md"):
    return client.post("/api/document-types/import-preview", files={"file": (name, text.encode())}, data={"target_key": target_key})


def test_md_upload_for_new_type_previews_without_saving(client):
    md = client.get("/api/document-types/brd/export").text.replace("doc_type: brd", "doc_type: brd_lite")
    preview = md_upload(client, md).json()
    assert preview["mode"] == "new"
    assert preview["diff"] is None
    assert client.get("/api/document-types/brd_lite").status_code == 404  # nothing saved yet


def test_md_upload_shows_changes_to_existing_type(client):
    md = client.get("/api/document-types/brd/export").text
    md = md.replace("- weight: low\n- critical: false\n- check: Key risks", "- weight: high\n- critical: true\n- check: Key risks")
    md = md.replace("## BRD-10", "## BRD-11: Glossary\n- weight: low\n- check: Terms defined.\n\n## BRD-10")
    preview = md_upload(client, md).json()
    assert preview["mode"] == "update"
    diff = preview["diff"]
    assert [r["id"] for r in diff["added"]] == ["BRD-11"]
    assert diff["changed"][0]["rule_id"] == "BRD-09"
    assert set(diff["changed"][0]["changed_fields"]) == {"weight", "critical"}
    assert diff["removed"] == []


def test_md_upload_into_chosen_type(client):
    md = client.get("/api/document-types/brd/export").text.replace("doc_type: brd", "doc_type: anything_else")
    preview = md_upload(client, md, target_key="brd").json()
    assert preview["mode"] == "update"
    assert preview["rulebook"]["doc_type"] == "brd"


def test_broken_md_upload_lists_problems(client):
    response = md_upload(client, "---\ndoc_type: x\ndisplay_name: X\n---\n## X-01: Rule\n- weight: huge\n")
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "rules.md" in detail["message"]
    assert "X-01: weight must be high, medium or low (got 'huge')." in detail["errors"]


def test_non_md_upload_rejected(client):
    assert "isn't a .md file" in md_upload(client, "x", name="rules.docx").json()["detail"]["message"]


# ---------- Prompt ----------


def test_prompt_without_api_key_explains_what_to_do(client):
    response = client.post("/api/document-types/brd/rules/draft", json={"instruction": "Add a glossary rule"})
    assert response.status_code == 400
    assert "no API key is set. Add ANTHROPIC_API_KEY" in response.json()["detail"]["message"]
    response = client.post("/api/document-types/prompt-preview", json={"instruction": "x", "display_name": "Data Migration Plan"})
    assert "no API key is set. Add ANTHROPIC_API_KEY" in response.json()["detail"]["message"]


def test_prompt_needs_a_name_for_new_type(client):
    response = client.post("/api/document-types/prompt-preview", json={"instruction": "x", "display_name": " "})
    assert "Please give the new document type a name." in response.json()["detail"]["message"]


def test_draft_rule_errors(client):
    unknown_rule = client.post("/api/document-types/brd/rules/draft", json={"instruction": "x", "rule_id": "BRD-99"})
    assert "There's no rule BRD-99" in unknown_rule.json()["detail"]["message"]
    unknown_type = client.post("/api/document-types/nope/rules/draft", json={"instruction": "x"})
    assert "No document type called 'nope'" in unknown_type.json()["detail"]["message"]
    empty = client.post("/api/document-types/brd/rules/draft", json={"instruction": "  "})
    assert "Please describe the rule" in empty.json()["detail"]["message"]


@pytest.fixture
def fake_ai(monkeypatch):
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    holder = SimpleNamespace(proposal=None)
    monkeypatch.setattr(llm, "_ask_ai", lambda system, user, fmt, problem, purpose, usage: holder.proposal)
    return holder


def proposed(rule_id, title, weight="medium", critical=False):
    return AIProposedRule(id=rule_id, title=title, weight=weight, critical=critical, check=f"Check {title}")


def single(title, weight="medium", critical=False, summary="Done."):
    return AIProposedSingleRule(title=title, weight=weight, critical=critical, check=f"Check {title}", summary=summary)


def test_ai_drafts_a_new_rule_with_the_next_id(client, fake_ai):
    fake_ai.proposal = single("Glossary", "low", summary="Added a glossary rule.")
    result = client.post("/api/document-types/brd/rules/draft", json={"instruction": "Add a glossary rule"}).json()
    assert result["rule"]["id"] == "BRD-11"
    assert result["rule"]["title"] == "Glossary"
    assert result["summary"] == "Added a glossary rule."
    assert result["original"] is None
    assert brd(client)["version"] == 1  # nothing saved


def test_ai_changes_one_rule_and_keeps_its_id(client, fake_ai):
    fake_ai.proposal = single("Risks with mitigations", "high", critical=True, summary="Made risks critical.")
    result = client.post("/api/document-types/brd/rules/draft", json={"instruction": "Make this critical", "rule_id": "BRD-09"}).json()
    assert result["rule"]["id"] == "BRD-09"
    assert result["rule"]["critical"] is True
    assert result["original"]["id"] == "BRD-09" and result["original"]["critical"] is False
    assert brd(client)["version"] == 1  # nothing saved


def test_prompt_new_type(client, fake_ai):
    fake_ai.proposal = AIProposedRulebook(
        display_name="Data Migration Plan", description="d", summary="Drafted 2 rules.",
        rules=[proposed(None, "Mapping", "high", True), proposed(None, "Rollback")],
    )
    preview = client.post("/api/document-types/prompt-preview", json={"instruction": "...", "display_name": "Data Migration Plan"}).json()
    assert preview["mode"] == "new"
    assert preview["rulebook"]["doc_type"] == "data_migration_plan"
    assert [r["id"] for r in preview["rulebook"]["rules"]] == ["DMP-01", "DMP-02"]
    saved = create(client, preview["rulebook"])
    assert saved.status_code == 201


# ---------- Part B (Excel) rules ----------


def test_ai_drafts_a_new_excel_rule(client, monkeypatch, frd_excel_rule):
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    prompts = []
    monkeypatch.setattr(llm, "_ask_ai", lambda system, user, fmt, problem, purpose, usage: prompts.append(user) or single("Joins sheet"))
    body = client.post("/api/document-types/frd/rules/draft", json={"instruction": "Joins need keys", "part": "excel"}).json()
    assert body["rule"]["id"] == "FRD-XL-02" and body["rule"]["part"] == "excel"
    assert "Part B (Excel) rule" in prompts[0]


def test_ai_change_keeps_an_excel_rules_part(client, fake_ai, frd_excel_rule):
    fake_ai.proposal = single("Field mapping sheet with types", "high", critical=True)
    body = client.post("/api/document-types/frd/rules/draft", json={"instruction": "Add data types", "rule_id": "FRD-XL-01"}).json()
    assert body["rule"]["id"] == "FRD-XL-01" and body["rule"]["part"] == "excel"


def test_new_document_rule_id_skips_excel_ids(client, fake_ai, frd_excel_rule):
    fake_ai.proposal = single("Glossary", "low")
    body = client.post("/api/document-types/frd/rules/draft", json={"instruction": "Add a glossary"}).json()
    assert body["rule"]["part"] == "document"
    assert body["rule"]["id"].startswith("FRD-") and "XL" not in body["rule"]["id"]
