from types import SimpleNamespace

import pytest

from app.config import PROJECT_ROOT, settings
from app.models import Review
from app.schemas import AIReviewOutput, AIRuleJudgement, AISuggestion
from app.services import llm, review_engine
from app.services.rulebook_editor import current_rulebook
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
    assert "categories" not in review and "category" not in review["rules"][0]
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


# ---------- PDF report ----------


def test_pdf_report(client):
    first = upload(client, "brd_weak.md", title="Invoice “Automation” BRD – v1")
    second = revise(client, first["document_id"], "brd_strong.docx")
    for review_id in (first["review_id"], second["review_id"]):
        response = client.get(f"/api/reviews/{review_id}/report")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content.startswith(b"%PDF")
        assert ".pdf" in response.headers["content-disposition"]


def test_pdf_report_errors(client, session):
    assert client.get("/api/reviews/999/report").status_code == 404
    review_id = upload(client)["review_id"]
    session.get(Review, review_id).status = "processing"
    session.commit()
    response = client.get(f"/api/reviews/{review_id}/report")
    assert response.status_code == 400
    assert "once the review has finished" in response.json()["detail"]


# ---------- Excel workbook (Part B) ----------

WORKBOOK = ("mapping.xlsx", (SAMPLES / "frd_mapping_sample.xlsx").read_bytes())


def upload_frd(client, workbook=None):
    files = {"file": ("frd.md", (SAMPLES / "brd_strong.md").read_bytes())}
    if workbook:
        files["workbook"] = workbook
    response = client.post("/api/documents", files=files, data={"document_type": "frd", "uploaded_by": "Jordan"})
    return client.get(f"/api/reviews/{response.json()['review_id']}").json()


def test_part_b_left_out_without_a_workbook(client, session, frd_excel_rule, fake_claude):
    document_rules = [r for r in current_rulebook(session, "frd").rules if r.part == "document"]
    fake_claude.responses.append(fake_response(AIReviewOutput(results=[judgement(r.id) for r in document_rules])))
    review = upload_frd(client)
    assert len(fake_claude.calls) == 1  # no workbook call
    assert review["score"] == 100 and review["passed"] is True  # the Excel rule isn't counted as failed
    assert review["rule_count"] == len(document_rules)
    assert review["excel_rules_left_out"] == 1
    assert review["workbook_filename"] is None
    assert review["document_subtotal"] == 100 and review["excel_subtotal"] is None
    assert {r["part"] for r in review["rules"]} == {"document"}
    assert review["prompt_version"] == "evaluate_rules_v1"


def test_workbook_reviewed_against_part_b(client, session, frd_excel_rule, fake_claude):
    document_rules = [r for r in current_rulebook(session, "frd").rules if r.part == "document"]
    fake_claude.responses.append(fake_response(AIReviewOutput(results=[judgement(r.id) for r in document_rules])))
    fake_claude.responses.append(fake_response(AIReviewOutput(results=[judgement("FRD-XL-01", "not_met")])))
    review = upload_frd(client, WORKBOOK)

    document_call, workbook_call = fake_claude.calls
    assert "<workbook>" not in document_call["messages"][0]["content"]
    assert "FRD-XL-01" not in document_call["messages"][0]["content"]
    workbook_prompt = workbook_call["messages"][0]["content"]
    assert "Rule FRD-XL-01" in workbook_prompt and "Rule FRD-01" not in workbook_prompt
    assert "<document>" in workbook_prompt  # for consistency rules
    assert "<workbook>" in workbook_prompt and "## Sheet: Field Mapping" in workbook_prompt
    assert "NOT the correctness of the data values" in workbook_call["system"]

    assert review["prompt_version"] == "evaluate_rules_v1 + evaluate_workbook_v1"
    assert review["workbook_filename"] == "mapping.xlsx"
    assert review["rule_count"] == len(document_rules) + 1 and review["excel_rules_left_out"] == 0
    assert review["rules"][-1]["rule_id"] == "FRD-XL-01" and review["rules"][-1]["part"] == "excel"
    assert review["document_subtotal"] == 100 and review["excel_subtotal"] == 0
    # one score for both parts; the critical Excel rule Not Met fails the whole document
    assert 80 <= review["score"] < 100
    assert review["passed"] is False
    assert review["critical_failures"] == [{"rule_id": "FRD-XL-01", "title": "Field mapping sheet"}]


def test_workbook_review_in_demo_mode(client, frd_excel_rule):
    review = upload_frd(client, WORKBOOK)
    assert review["status"] == "complete" and review["is_demo"] is True
    [excel] = [r for r in review["rules"] if r["part"] == "excel"]
    assert excel["status"] == "met"  # the sample workbook has a Field Mapping sheet
    assert excel["location"].startswith("Sheet: ")  # the sheet the demo reviewer found it on
    assert review["excel_subtotal"] == 100


def test_rules_in_review():
    rules_json = [
        {"id": "A-1", "title": "a", "weight": "high", "check": "x"},
        {"id": "XL-1", "title": "b", "part": "excel", "weight": "low", "check": "x"},
    ]
    assert [r.id for r in review_engine.rules_in_review(rules_json, has_workbook=True)] == ["A-1", "XL-1"]
    assert [r.id for r in review_engine.rules_in_review(rules_json, has_workbook=False)] == ["A-1"]


def test_pdf_report_grouped_by_part(client, session, frd_excel_rule):
    from app.services.report_pdf import _rules_by_part

    with_workbook = review_engine.get_review(session, upload_frd(client, WORKBOOK)["id"])
    response = client.get(f"/api/reviews/{with_workbook.id}/report")
    assert response.status_code == 200 and response.content.startswith(b"%PDF")
    [(document_heading, _), (excel_heading, [excel_rule])] = _rules_by_part(with_workbook)
    assert document_heading.startswith(" - Part A: Document (subtotal ")
    assert excel_heading == " - Part B: Excel workbook (subtotal 100)" and excel_rule.rule_id == "FRD-XL-01"
    without = review_engine.get_review(session, upload_frd(client)["id"])
    [(heading, _)] = _rules_by_part(without)
    assert heading == ""  # one part: no part headings
    assert client.get(f"/api/reviews/{without.id}/report").status_code == 200
