"""API endpoints for the Usage Analytics page: AI token usage, cost, and model prices."""

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_session
from app.services import usage
from app.services.usage import PriceError

router = APIRouter(prefix="/api/usage", tags=["Usage Analytics"])


class PriceUpdate(BaseModel):
    """US dollars per 1 million tokens."""

    model: str
    input_per_million: float
    cached_input_per_million: float
    output_per_million: float
    updated_by: str


def dates(
    date_from: date | None = Query(None, alias="from", description="YYYY-MM-DD"),
    date_to: date | None = Query(None, alias="to", description="YYYY-MM-DD"),
) -> dict:
    return {"date_from": date_from, "date_to": date_to}


@router.get("/summary")
def summary(d: dict = Depends(dates), session: Session = Depends(get_session)):
    """Totals for the summary cards: calls, tokens, cost, average cost per review."""
    return usage.summary(session, **d)


@router.get("/trend")
def trend(
    period: Literal["week", "month"] = "week",
    d: dict = Depends(dates),
    session: Session = Depends(get_session),
):
    """Calls, tokens and cost per week (starting Monday) or per month."""
    return usage.trend(session, period, **d)


@router.get("/by-model")
def by_model(d: dict = Depends(dates), session: Session = Depends(get_session)):
    return usage.by_model(session, **d)


@router.get("/by-purpose")
def by_purpose(d: dict = Depends(dates), session: Session = Depends(get_session)):
    return usage.by_purpose(session, **d)


@router.get("/prices")
def list_prices(session: Session = Depends(get_session)):
    """Model prices, plus models in use that have no price yet."""
    return usage.list_prices(session)


@router.put("/prices")
def save_price(body: PriceUpdate, session: Session = Depends(get_session)):
    """Add or change a model's price."""
    try:
        return usage.save_price(session, **body.model_dump())
    except PriceError as e:
        raise HTTPException(400, str(e))
