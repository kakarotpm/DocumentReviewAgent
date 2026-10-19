from types import SimpleNamespace

import pytest

from app.config import PROJECT_ROOT, settings
from app.models import Review
from app.schemas import AIReviewOutput, AIRuleJudgement, AISuggestion
from app.services import llm, review_engine
from app.services.status import document_status

SAMPLES = PROJECT_ROOT / "samples"


def upload(client, name="brd_strong.md", document_type="brd", **fields):
    form = {"document_type": document_type, "uploaded_by": "Jordan", **fields}
    response = client.post("/api/documents", files={"file": (name, (SAMPLES / name).read_bytes())}, data=form)
    assert response.status_code == 201, response.text
    return response.json()


def revise(client, document_id, name):
    response = client.post(f"/api/documents/{document_id}/versions", files={"file": (name, (SAMPLES / name).read_bytes())})
    assert response.status_code == 201, response.text
    return response.json()


# ---------- A full review (demo mode) ----------


def test_review_results_for_strong_brd(client):
    review = client.get(f"/api/reviews/{upload(client)['review_id']}").json()
    assert review["status"] == "complete"
    assert review["is_demo"] is True
    assert review["passed"] is True
    assert review["score"] >= 80
    assert len(review["rules"]) == 10
    assert {c["category"] for c in review["categories"]} >= {"Scope", "Objectives"}
    assert review["comparison"] is None  # version 1 has nothing to compare with


def test_weak_brd_fails_with_critical_rule(client):
    review = client.get(f"/api/reviews/{upload(client, 'brd_weak.md')['review_id']}").json()
    assert review["passed"] is False
    assert any(c["rule_id"] == "BRD-03" for c in review["critical_failures"])
    suggestions = [s for r in review["rules"] for s in r["suggestions"]]
    assert {s["type"] for s in suggestions} <= {"add", "change", "delete"}
    assert any(s["type"] == "add" for s in suggestions)


def test_suggestion_state_can_be_updated(client):
    review = client.get(f"/api/reviews/{upload(client, 'brd_weak.md')['review_id']}").json()
    suggestion_id = next(s["id"] for r in review["rules"] for s in r["suggestions"])
    response = client.patch(f"/api/suggestions/{suggestion_id}", json={"user_state": "done"})
    assert response.status_code == 200 and response.json()["user_state"] == "done"
    assert client.patch(f"/api/suggestions/{suggestion_id}", json={"user_state": "maybe"}).status_code == 422


def test_rerun_creates_a_new_review(client):
    first = upload(client)["review_id"]
    rerun = client.post(f"/api/reviews/{first}/rerun").json()
    assert rerun["id"] != first
    assert client.get(f"/api/reviews/{rerun['id']}").json()["status"] == "complete"


def test_unknown_review(client):
    assert client.get("/api/reviews/999").status_code == 404


def test_interrupted_reviews_are_marked_as_errors(session):
    from app.models import Document, DocumentType, DocumentVersion

    doc_type = session.query(DocumentType).first()
    document = Document(title="t", document_type=doc_type, uploaded_by="x")
    version = DocumentVersion(version_number=1, original_filename="a.md", file_type="md", extracted_text="x")
    document.versions.append(version)
    session.add(Review(document_version=version, rulebook_version=doc_type.latest_version, status="processing"))
    session.add(document)
    session.commit()
    assert review_engine.mark_interrupted_reviews(session) == 1
    assert "Re-run review" in session.query(Review).one().error_message


# ---------- Versions and statuses ----------


def test_failed_then_passed_is_corrected(client):
    first = upload(client, "brd_weak.md")
    second = revise(client, first["document_id"], "brd_strong.md")
    assert second["version_number"] == 2

    review = client.get(f"/api/reviews/{second['review_id']}").json()
    comparison = review["comparison"]
    assert comparison["previous_version_number"] == 1
    assert comparison["score_change"] > 0
    assert comparison["rules_updated"] is False
    assert any(r["rule_id"] == "BRD-03" for r in comparison["newly_met"])

    assert client.get(f"/api/documents/{first['document_id']}").json()["status"] == "Corrected"


def test_revised_version_uses_latest_rulebook_and_flags_it(client):
    first = upload(client, "brd_weak.md")
    rulebook = client.get("/api/document-types/brd").json()
    rulebook["rules"][0]["weight"] = "high"
    save = client.put("/api/document-types/brd", json={"rulebook": {**rulebook, "doc_type": "brd"}, "changed_by": "Lead"})
    assert save.status_code == 200, save.text
    second = revise(client, first["document_id"], "brd_strong.md")
    review = client.get(f"/api/reviews/{second['review_id']}").json()
    assert review["rulebook_version"] == 2
    assert review["comparison"]["rules_updated"] is True


def test_revision_errors(client):
    assert client.post("/api/documents/999/versions", files={"file": ("a.md", b"x" * 100)}).status_code == 404
    first = upload(client)
    bad = client.post(f"/api/documents/{first['document_id']}/versions", files={"file": ("a.png", b"x" * 100)})
    assert bad.status_code == 400


@pytest.mark.parametrize(
    "history, expected",
    [
        ([], "In review"),
        ([("queued", None)], "In review"),
        ([("processing", None)], "In review"),
        ([("error", None)], "Error"),
        ([("complete", True)], "Passed"),
        ([("complete", False)], "Failed"),
        ([("complete", False), ("complete", True)], "Corrected"),
        ([("complete", True), ("complete", False)], "Failed"),
        ([("complete", True), ("complete", True)], "Passed"),
        ([("complete", False), ("error", None), ("complete", True)], "Corrected"),
        ([("complete", False), ("processing", None)], "In review"),
    ],
)
def test_document_status(history, expected):
    assert document_status(history) == expected


def test_documents_list_filters_and_sorting(client):
    upload(client, "brd_strong.md", project_name="AP")
    upload(client, "brd_weak.md", project_name="Payroll")
    all_docs = client.get("/api/documents").json()
    assert len(all_docs) == 2
    assert [d["title"] for d in client.get("/api/documents?search=WEAK").json()] == ["brd_weak"]
    assert [d["status"] for d in client.get("/api/documents?status=Failed").json()] == ["Failed"]
    assert [d["project_name"] for d in client.get("/api/documents?project=AP").json()] == ["AP"]
    by_score = client.get("/api/documents?sort=score&descending=false").json()
    assert by_score[0]["latest_score"] < by_score[1]["latest_score"]
    assert client.get("/api/documents/projects").json() == ["AP", "Payroll"]


# ---------- The real-AI path, with Claude replaced by a fake ----------


def fake_response(output, stop_reason="end_turn"):
    return SimpleNamespace(stop_reason=stop_reason, parsed_output=output)


def judgement(rule_id, status="met"):
    return AIRuleJudgement(rule_id=rule_id, status=status, evidence="e", location="l", explanation="x", suggestions=[])


@pytest.fixture
def fake_claude(monkeypatch):
    """Pretend an API key is set and capture calls instead of calling Claude."""
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    responses = []
    calls = []

    class FakeMessages:
        def parse(self, **kwargs):
            calls.append(kwargs)
            return responses.pop(0)

    class FakeClient:
        def __init__(self, **kwargs):
            self.messages = FakeMessages()

    monkeypatch.setattr(llm.anthropic, "Anthropic", FakeClient)
    return SimpleNamespace(responses=responses, calls=calls)


def brd_rules(session):
    from app.services.rulebook_editor import current_rulebook

    return current_rulebook(session, "brd").rules


def test_claude_answer_is_used(session, fake_claude):
    rules = brd_rules(session)
    fake_claude.responses.append(fake_response(AIReviewOutput(results=[judgement(r.id) for r in rules])))
    output, model, prompt = llm.evaluate_rules("doc text", rules, "BRD")
    assert len(output.results) == 10
    assert model == settings.anthropic_model and prompt == "evaluate_rules_v1"
    call = fake_claude.calls[0]
    assert "<document>\ndoc text\n</document>" in call["messages"][0]["content"]
    assert call["output_format"] is AIReviewOutput


def test_claude_missing_rule_is_retried_once(session, fake_claude):
    rules = brd_rules(session)
    incomplete = AIReviewOutput(results=[judgement(r.id) for r in rules[:-1]])
    complete = AIReviewOutput(results=[judgement(r.id) for r in rules])
    fake_claude.responses.extend([fake_response(incomplete), fake_response(complete)])
    output, _, _ = llm.evaluate_rules("doc", rules, "BRD")
    assert len(output.results) == 10
    assert len(fake_claude.calls) == 2


def test_claude_invalid_twice_gives_friendly_error(session, fake_claude):
    rules = brd_rules(session)
    fake_claude.responses.extend([fake_response(None, "max_tokens"), fake_response(None, "max_tokens")])
    with pytest.raises(llm.AIError, match="incomplete twice"):
        llm.evaluate_rules("doc", rules, "BRD")


def test_claude_refusal_gives_friendly_error(session, fake_claude):
    fake_claude.responses.append(fake_response(None, "refusal"))
    with pytest.raises(llm.AIError, match="declined"):
        llm.evaluate_rules("doc", brd_rules(session), "BRD")


def test_ai_error_is_saved_on_the_review(client, fake_claude):
    fake_claude.responses.extend([fake_response(None, "max_tokens"), fake_response(None, "max_tokens")])
    review = client.get(f"/api/reviews/{upload(client)['review_id']}").json()
    assert review["status"] == "error"
    assert "Re-run review" in review["error_message"]
    assert client.get(f"/api/documents/{review['document_id']}").json()["status"] == "Error"


def test_suggestions_from_ai_are_saved(client, session, fake_claude):
    rules = brd_rules(session)
    results = [judgement(r.id) for r in rules]
    results[3] = AIRuleJudgement(
        rule_id=rules[3].id, status="not_met", evidence="none", location="Not found", explanation="x",
        suggestions=[AISuggestion(type="add", location="After 3", proposed_text="3.2 Out of scope", rationale="r")],
    )
    fake_claude.responses.append(fake_response(AIReviewOutput(results=results)))
    review = client.get(f"/api/reviews/{upload(client)['review_id']}").json()
    assert review["is_demo"] is False
    assert review["passed"] is False  # BRD-04 is critical and not met
    [suggestion] = review["rules"][3]["suggestions"]
    assert suggestion["proposed_text"] == "3.2 Out of scope"
