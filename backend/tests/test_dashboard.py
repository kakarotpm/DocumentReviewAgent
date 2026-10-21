from datetime import date, timedelta

from app.models import Review
from tests.test_reviews import revise, upload


def seed(client):
    """Four documents (demo reviewer: strong sample passes, weak sample fails):
    A: weak -> strong   = Corrected      B: strong = Passed
    C: weak (Payroll)   = Failed         D: strong -> weak = Failed
    Completed reviews: 6, of which 3 passed (A v2, B, D v1).
    """
    a = upload(client, "brd_weak.md", project_name="AP")
    revise(client, a["document_id"], "brd_strong.md")
    upload(client, "brd_strong.md", project_name="AP")
    upload(client, "brd_weak.md", project_name="Payroll")
    d = upload(client, "brd_strong.md", project_name="AP")
    revise(client, d["document_id"], "brd_weak.md")


def get(client, path, **params):
    response = client.get(f"/api/dashboard/{path}", params=params)
    assert response.status_code == 200, response.text
    return response.json()


def test_summary_counts_match_the_data(client):
    seed(client)
    summary = get(client, "summary")
    assert summary["documents"] == 4
    assert summary["reviews_completed"] == 6
    assert (summary["passed"], summary["failed"], summary["corrected"]) == (1, 2, 1)
    assert summary["pass_rate"] == 50

    # The same statuses the Documents page shows.
    statuses = [d["status"] for d in client.get("/api/documents").json()]
    assert statuses.count("Passed") == summary["passed"]
    assert statuses.count("Failed") == summary["failed"]
    assert statuses.count("Corrected") == summary["corrected"]


def test_average_score_matches_reviews(client, session):
    seed(client)
    scores = [r.score for r in session.query(Review).filter(Review.status == "complete")]
    assert get(client, "summary")["average_score"] == round(sum(scores) / len(scores), 1)


def test_filters(client):
    seed(client)
    payroll = get(client, "summary", project="Payroll")
    assert (payroll["documents"], payroll["failed"], payroll["reviews_completed"]) == (1, 1, 1)
    assert get(client, "summary", type="frd")["documents"] == 0
    tomorrow = (date.today() + timedelta(days=2)).isoformat()
    assert get(client, "summary", **{"from": tomorrow})["reviews_completed"] == 0
    assert get(client, "summary", **{"to": tomorrow})["reviews_completed"] == 6


def test_empty_database(client):
    summary = get(client, "summary")
    assert summary["documents"] == 0 and summary["pass_rate"] is None and summary["average_score"] is None
    assert get(client, "trends") == []
    assert sum(b["reviews"] for b in get(client, "score-distribution")) == 0
    assert get(client, "top-failed-rules") == []


def test_charts(client):
    seed(client)
    [by_type] = get(client, "pass-fail-by-type")
    assert (by_type["passed"], by_type["failed"]) == (3, 3)

    [week] = get(client, "trends")
    assert week["reviews"] == 6 and week["pass_rate"] == 50

    buckets = get(client, "score-distribution")
    assert len(buckets) == 10 and buckets[-1]["range"] == "90–100"
    assert sum(b["reviews"] for b in buckets) == 6

    top = get(client, "top-failed-rules")
    assert len(top) <= 10
    assert top == sorted(top, key=lambda r: -r["times_not_met"])
    assert top[0]["times_not_met"] == 3  # the weak sample was reviewed 3 times

    affected = get(client, f"top-failed-rules/{top[0]['rule_id']}/documents")
    assert len(affected) == top[0]["times_not_met"]

    recent = get(client, "recent-reviews")
    assert len(recent) == 6 and recent[0]["review_id"] > recent[-1]["review_id"]
