"""API endpoints for the dashboard. All accept the same filters: from, to, type, project."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_session
from app.services import dashboard

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


def filters(
    date_from: date | None = Query(None, alias="from", description="YYYY-MM-DD"),
    date_to: date | None = Query(None, alias="to", description="YYYY-MM-DD"),
    doc_type: str = Query("", alias="type", description="Document type key, e.g. brd"),
    project: str = "",
) -> dict:
    return {"date_from": date_from, "date_to": date_to, "doc_type": doc_type, "project": project}


@router.get("/summary")
def summary(f: dict = Depends(filters), session: Session = Depends(get_session)):
    """Numbers for the summary cards."""
    return dashboard.summary(session, **f)


@router.get("/pass-fail-by-type")
def pass_fail_by_type(f: dict = Depends(filters), session: Session = Depends(get_session)):
    return dashboard.pass_fail_by_type(session, **f)


@router.get("/trends")
def trends(f: dict = Depends(filters), session: Session = Depends(get_session)):
    """Reviews and pass rate per week."""
    return dashboard.trends(session, **f)


@router.get("/score-distribution")
def score_distribution(f: dict = Depends(filters), session: Session = Depends(get_session)):
    return dashboard.score_distribution(session, **f)


@router.get("/top-failed-rules")
def top_failed_rules(f: dict = Depends(filters), session: Session = Depends(get_session)):
    """The 10 rules most often Not Met."""
    return dashboard.top_failed_rules(session, **f)


@router.get("/top-failed-rules/{rule_id}/documents")
def documents_failing_rule(rule_id: str, f: dict = Depends(filters), session: Session = Depends(get_session)):
    """The reviews where this rule was Not Met."""
    return dashboard.documents_failing_rule(session, rule_id, **f)


@router.get("/recent-reviews")
def recent_reviews(f: dict = Depends(filters), session: Session = Depends(get_session)):
    return dashboard.recent_reviews(session, **f)
