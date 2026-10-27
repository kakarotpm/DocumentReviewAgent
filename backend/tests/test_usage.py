from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest

from app.config import settings
from app.models import AIUsage, ModelPrice
from app.schemas import AIReviewOutput, AIRuleJudgement
from app.services import llm, usage
from app.services.rulebook_editor import current_rulebook
from app.services.usage import PriceError

SAMPLE = "# BRD\n" + "Business requirements for invoice matching. " * 10


def add_call(session, day, model="gpt-test", purpose="document_review", review_id=None, tokens=(1000, 0, 100), cost=None):
    input_tokens, cached, output_tokens = tokens
    session.add(AIUsage(
        created_at=datetime.fromisoformat(day).replace(tzinfo=timezone.utc), provider="openai", model=model,
        purpose=purpose, review_id=review_id, input_tokens=input_tokens, cached_input_tokens=cached,
        output_tokens=output_tokens, cost_usd=cost,
    ))
    session.commit()


def set_price(session, model="gpt-test", prices=(2.50, 0.25, 15.00)):
    return usage.save_price(session, model, *prices, updated_by="Lead")


# ---------- Cost ----------


def test_cost_formula():
    price = SimpleNamespace(input_per_million=2.50, cached_input_per_million=0.25, output_per_million=15.00)
    # 1,000,000 input of which 200,000 cached, 100,000 output:
    # 800,000 x 2.50 + 200,000 x 0.25 + 100,000 x 15.00 = (2,000,000 + 50,000 + 1,500,000) / 1,000,000 = 3.55
    assert usage.call_cost(price, 1_000_000, 200_000, 100_000) == pytest.approx(3.55)
    assert usage.call_cost(None, 1000, 0, 100) is None  # no price: unknown, not free


def test_record_prices_each_call_at_todays_price(session):
    set_price(session)
    calls = [llm.TokenUsage("openai", "gpt-test", "document_review", 1_000_000, 0, 0),
             llm.TokenUsage("openai", "unpriced-model", "draft_rule", 500, 0, 50)]
    usage.record(session, calls, review_id=None)
    rows = session.query(AIUsage).order_by(AIUsage.id).all()
    assert rows[0].cost_usd == pytest.approx(2.50)
    assert rows[1].cost_usd is None


def test_later_price_change_does_not_rewrite_past_cost(session):
    set_price(session, prices=(2.50, 0.25, 15.00))
    usage.record(session, [llm.TokenUsage("openai", "gpt-test", "document_review", 1_000_000, 0, 0)])
    set_price(session, prices=(10.00, 1.00, 40.00))
    assert usage.summary(session)["cost"] == pytest.approx(2.50)


def test_calls_without_a_price_use_todays_price_once_set(session):
    add_call(session, "2026-10-20", tokens=(1_000_000, 0, 0))  # recorded before any price existed
    assert usage.summary(session)["cost"] is None
    assert usage.summary(session)["unpriced_calls"] == 1
    set_price(session)
    assert usage.summary(session)["cost"] == pytest.approx(2.50)
    assert usage.summary(session)["unpriced_calls"] == 0


# ---------- Totals, trend, breakdowns ----------


def test_summary_and_date_filter(session):
    add_call(session, "2026-10-05", review_id=1, tokens=(1000, 200, 100), cost=0.01)
    add_call(session, "2026-10-05", purpose="workbook_review", review_id=1, tokens=(500, 0, 50), cost=0.02)
    add_call(session, "2026-10-20", purpose="draft_rule", tokens=(300, 0, 30), cost=0.03)
    s = usage.summary(session)
    assert s["calls"] == 3
    assert s["input_tokens"] == 1800 and s["cached_input_tokens"] == 200 and s["output_tokens"] == 180
    assert s["total_tokens"] == 1980
    assert s["cost"] == pytest.approx(0.06)
    assert s["reviews"] == 1 and s["cost_per_review"] == pytest.approx(0.03)  # drafting isn't a review
    october_20 = usage.summary(session, date_from=date(2026, 10, 10), date_to=date(2026, 10, 31))
    assert october_20["calls"] == 1 and october_20["cost_per_review"] is None


def test_weekly_trend_fills_empty_weeks(session):
    add_call(session, "2026-10-06", cost=0.10)  # Tuesday: week of Mon 5 Oct
    add_call(session, "2026-10-08", cost=0.20)
    add_call(session, "2026-10-21", cost=0.40)  # week of Mon 19 Oct
    weeks = usage.trend(session, "week")
    assert [w["period_start"] for w in weeks] == ["2026-10-05", "2026-10-12", "2026-10-19"]
    assert [w["cost"] for w in weeks] == pytest.approx([0.30, 0.0, 0.40])
    assert [w["calls"] for w in weeks] == [2, 0, 1]
    assert weeks[0]["tokens"] == 2200


def test_monthly_trend_covers_the_chosen_range(session):
    add_call(session, "2026-08-15", cost=1.0)
    add_call(session, "2026-10-01", cost=2.0)
    months = usage.trend(session, "month", date_from=date(2026, 7, 10), date_to=date(2026, 10, 31))
    assert [m["period_start"] for m in months] == ["2026-07-01", "2026-08-01", "2026-09-01", "2026-10-01"]
    assert [m["cost"] for m in months] == pytest.approx([0.0, 1.0, 0.0, 2.0])
    assert usage.trend(session, "month", date_from=date(2025, 1, 1), date_to=date(2025, 2, 1)) == []  # no usage


def test_breakdowns(session):
    set_price(session, "gpt-test")
    add_call(session, "2026-10-05", model="gpt-test", cost=0.5)
    add_call(session, "2026-10-05", model="other-model", purpose="draft_rules")
    [priced, unpriced] = usage.by_model(session)
    assert priced["model"] == "gpt-test" and priced["has_price"] is True and priced["cost"] == pytest.approx(0.5)
    assert unpriced["model"] == "other-model" and unpriced["has_price"] is False and unpriced["cost"] is None
    assert {r["purpose"] for r in usage.by_purpose(session)} == {"document_review", "draft_rules"}


# ---------- Prices ----------


def test_default_prices_only_on_first_run(session):
    usage.seed_default_prices(session)
    assert session.query(ModelPrice).filter_by(model="gpt-5.4-2").one().output_per_million == 15.00
    set_price(session, "gpt-5.4-2", (1, 1, 1))
    usage.seed_default_prices(session)  # doesn't overwrite your edits
    assert session.query(ModelPrice).filter_by(model="gpt-5.4-2").one().output_per_million == 1


def test_price_validation(session):
    with pytest.raises(PriceError, match="model name"):
        usage.save_price(session, " ", 1, 1, 1, updated_by="Lead")
    with pytest.raises(PriceError, match="your name"):
        usage.save_price(session, "m", 1, 1, 1, updated_by=" ")
    with pytest.raises(PriceError, match="negative"):
        usage.save_price(session, "m", -1, 1, 1, updated_by="Lead")


def test_prices_api_lists_models_missing_a_price(client, session, monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "k")
    monkeypatch.setattr(settings, "openai_model", "gpt-current")
    add_call(session, "2026-10-05", model="gpt-old")
    body = client.get("/api/usage/prices").json()
    assert body["missing"] == ["gpt-current", "gpt-old"]
    assert body["current_model"] == "gpt-current" and body["current_provider"] == "OpenAI (GPT)"
    saved = client.put("/api/usage/prices", json={"model": "gpt-current", "input_per_million": 2.5,
                                                  "cached_input_per_million": 0.25, "output_per_million": 15, "updated_by": "Lead"})
    assert saved.status_code == 200 and saved.json()["updated_by"] == "Lead"
    assert client.get("/api/usage/prices").json()["missing"] == ["gpt-old"]
    bad = client.put("/api/usage/prices", json={"model": "x", "input_per_million": -1, "cached_input_per_million": 0,
                                                "output_per_million": 0, "updated_by": "Lead"})
    assert bad.status_code == 400 and "negative" in bad.json()["detail"]


def test_usage_api(client, session):
    add_call(session, "2026-10-06", cost=0.1)
    assert client.get("/api/usage/summary?from=2026-10-01&to=2026-10-31").json()["calls"] == 1
    assert client.get("/api/usage/trend?period=month").json()[0]["period_start"] == "2026-10-01"
    assert client.get("/api/usage/trend?period=year").status_code == 422
    assert client.get("/api/usage/by-model").json()[0]["model"] == "gpt-test"
    assert client.get("/api/usage/by-purpose").json()[0]["purpose"] == "document_review"


# ---------- Usage is saved from real AI calls (OpenAI replaced by a fake) ----------


def openai_answer(parsed, input_tokens=1200, cached=200, output_tokens=300):
    return SimpleNamespace(
        output=[SimpleNamespace(type="message", content=[SimpleNamespace(type="output_text")])],
        output_parsed=parsed, status="completed", incomplete_details=None,
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens,
                              input_tokens_details=SimpleNamespace(cached_tokens=cached)),
    )


@pytest.fixture
def fake_openai(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "openai_model", "gpt-test")
    answers = []

    class FakeClient:
        def __init__(self, **kwargs):
            self.responses = SimpleNamespace(parse=lambda **kw: answers.pop(0))

    monkeypatch.setattr(llm.openai, "OpenAI", FakeClient)
    return answers


def results_for(session, key="brd", status="met"):
    return AIReviewOutput(results=[
        AIRuleJudgement(rule_id=r.id, status=status, evidence="e", location="l", explanation="x", suggestions=[])
        for r in current_rulebook(session, key).rules
    ])


def test_a_review_saves_its_token_usage(client, session, fake_openai):
    set_price(session)
    fake_openai.append(openai_answer(results_for(session)))
    upload = client.post("/api/documents", files={"file": ("brd.md", SAMPLE.encode())},
                         data={"document_type": "brd", "uploaded_by": "Jordan"}).json()
    [row] = session.query(AIUsage).all()
    assert row.review_id == upload["review_id"] and row.purpose == "document_review"
    assert (row.provider, row.model) == ("openai", "gpt-test")
    assert (row.input_tokens, row.cached_input_tokens, row.output_tokens) == (1200, 200, 300)
    assert row.cost_usd == pytest.approx((1000 * 2.50 + 200 * 0.25 + 300 * 15.00) / 1_000_000)


def test_a_failed_review_still_saves_the_tokens_it_used(client, session, fake_openai):
    incomplete = AIReviewOutput(results=results_for(session).results[:-1])  # one rule missing, twice
    fake_openai.extend([openai_answer(incomplete), openai_answer(incomplete)])
    upload = client.post("/api/documents", files={"file": ("brd.md", SAMPLE.encode())},
                         data={"document_type": "brd", "uploaded_by": "Jordan"}).json()
    assert client.get(f"/api/reviews/{upload['review_id']}").json()["status"] == "error"
    assert session.query(AIUsage).count() == 2  # both attempts were paid for


def test_anthropic_tokens_include_cache_reads():
    response = SimpleNamespace(usage=SimpleNamespace(input_tokens=100, cache_read_input_tokens=900,
                                                     cache_creation_input_tokens=None, output_tokens=50))
    assert llm._anthropic_tokens(response) == (1000, 900, 50)


def test_demo_mode_saves_no_usage(client, session):
    client.post("/api/documents", files={"file": ("brd.md", SAMPLE.encode())}, data={"document_type": "brd", "uploaded_by": "J"})
    assert session.query(AIUsage).count() == 0
