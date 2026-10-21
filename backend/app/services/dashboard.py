"""Dashboard numbers. The SQL lives in dashboard.sql so it can be read on its own."""

from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

SQL_FILE = Path(__file__).with_name("dashboard.sql")
STATUSES = ["Passed", "Failed", "Corrected", "In review", "Error"]


def _load_queries() -> dict[str, str]:
    """Split dashboard.sql into {name: query} using its '-- name:' lines."""
    queries, name, lines = {}, None, []
    for line in SQL_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("-- name:"):
            if name:
                queries[name] = "\n".join(lines)
            name, lines = line.removeprefix("-- name:").strip(), []
        elif name and not line.lstrip().startswith("--"):  # comments are for people, not the database
            lines.append(line)
    if name:
        queries[name] = "\n".join(lines)
    return queries


QUERIES = _load_queries()


def _filters(doc_type="", project="", date_from: date | None = None, date_to: date | None = None) -> dict:
    return {
        "doc_type": doc_type or "",
        "project": project or "",
        "date_from": date_from.isoformat() if date_from else "",
        "date_to": date_to.isoformat() if date_to else "",
    }


def _rows(session: Session, name: str, params: dict) -> list[dict]:
    return [dict(row._mapping) for row in session.execute(text(QUERIES[name]), params)]


def summary(session: Session, **filters) -> dict:
    params = _filters(**filters)
    reviews = _rows(session, "review_summary", params)[0]
    statuses = {row["status"]: row["documents"] for row in _rows(session, "document_statuses", params)}
    completed = reviews["reviews_completed"] or 0
    passed = reviews["reviews_passed"] or 0
    return {
        "documents": sum(statuses.values()),
        "reviews_completed": completed,
        "passed": statuses.get("Passed", 0),
        "failed": statuses.get("Failed", 0),
        "corrected": statuses.get("Corrected", 0),
        "in_review": statuses.get("In review", 0),
        "errors": statuses.get("Error", 0),
        "pass_rate": round(passed / completed * 100) if completed else None,
        "average_score": reviews["average_score"],
    }


def pass_fail_by_type(session: Session, **filters) -> list[dict]:
    return _rows(session, "pass_fail_by_type", _filters(**filters))


def trends(session: Session, **filters) -> list[dict]:
    """Reviews and pass rate per week (weeks start on Monday). Weeks with no reviews are included."""
    days = _rows(session, "reviews_per_day", _filters(**filters))
    weeks: dict[date, dict] = {}
    for row in days:
        day = date.fromisoformat(str(row["day"]))
        week_start = day - timedelta(days=day.weekday())
        week = weeks.setdefault(week_start, {"reviews": 0, "passed": 0})
        week["reviews"] += row["reviews"]
        week["passed"] += row["passed"]
    if not weeks:
        return []
    result = []
    week_start, last = min(weeks), max(weeks)
    while week_start <= last:
        week = weeks.get(week_start, {"reviews": 0, "passed": 0})
        result.append({
            "week_start": week_start.isoformat(),
            "reviews": week["reviews"],
            "pass_rate": round(week["passed"] / week["reviews"] * 100) if week["reviews"] else None,
        })
        week_start += timedelta(days=7)
    return result


def score_distribution(session: Session, **filters) -> list[dict]:
    """Always all ten buckets, so the chart's x-axis doesn't jump around."""
    counts = {row["bucket"]: row["reviews"] for row in _rows(session, "score_distribution", _filters(**filters))}
    return [
        {"range": f"{b * 10}–{b * 10 + 9 if b < 9 else 100}", "from": b * 10, "reviews": counts.get(b, 0)}
        for b in range(10)
    ]


def top_failed_rules(session: Session, **filters) -> list[dict]:
    return _rows(session, "top_failed_rules", _filters(**filters))


def documents_failing_rule(session: Session, rule_id: str, **filters) -> list[dict]:
    return _rows(session, "documents_failing_rule", {**_filters(**filters), "rule_id": rule_id})


def recent_reviews(session: Session, **filters) -> list[dict]:
    return _rows(session, "recent_reviews", _filters(**filters))
