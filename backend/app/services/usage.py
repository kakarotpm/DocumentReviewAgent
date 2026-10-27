"""AI token usage and cost: saving each call's usage, model prices, and the Usage Analytics numbers.

The SQL lives in usage.sql so it can be read on its own (same layout as dashboard.sql).
"""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import AIUsage, ModelPrice
from app.services import llm

SQL_FILE = Path(__file__).with_name("usage.sql")

# Loaded into an empty price table on first run. Public list price on 2026-10-27; check the
# provider's pricing page (or your Azure agreement) and edit on the Usage Analytics page.
DEFAULT_PRICES = [
    {"model": "gpt-5.4-2", "input_per_million": 2.50, "cached_input_per_million": 0.25, "output_per_million": 15.00},
]
DEFAULT_PRICES_BY = "DocReview default (OpenAI list price, 27 Oct 2026)"
PERIODS = ("week", "month")


class PriceError(ValueError):
    """A price can't be saved. The message tells the user what to fix."""


def _load_queries() -> dict[str, str]:
    """Split usage.sql into {name: query} using its '-- name:' lines."""
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


def _rows(session: Session, name: str, date_from: date | None, date_to: date | None) -> list[dict]:
    params = {"date_from": date_from.isoformat() if date_from else "", "date_to": date_to.isoformat() if date_to else ""}
    return [dict(row._mapping) for row in session.execute(text(QUERIES[name]), params)]


# ---------- Saving usage ----------


def call_cost(price: ModelPrice | None, input_tokens: int, cached_input_tokens: int, output_tokens: int) -> float | None:
    """Cost in US dollars, or None when there's no price for the model. Same formula as usage.sql."""
    if price is None:
        return None
    return (
        (input_tokens - cached_input_tokens) * price.input_per_million
        + cached_input_tokens * price.cached_input_per_million
        + output_tokens * price.output_per_million
    ) / 1_000_000


def record(session: Session, calls: list[llm.TokenUsage], review_id: int | None = None) -> None:
    """Save the AI calls collected during a review or a rule draft, each priced at today's price."""
    if not calls:
        return
    prices = {p.model: p for p in session.scalars(select(ModelPrice))}
    for c in calls:
        session.add(AIUsage(
            provider=c.provider,
            model=c.model,
            purpose=c.purpose,
            review_id=review_id,
            input_tokens=c.input_tokens,
            cached_input_tokens=c.cached_input_tokens,
            output_tokens=c.output_tokens,
            cost_usd=call_cost(prices.get(c.model), c.input_tokens, c.cached_input_tokens, c.output_tokens),
        ))
    session.commit()


# ---------- Prices ----------


def seed_default_prices(session: Session) -> None:
    """On first run only: start the price table with the known list prices."""
    if session.scalar(select(ModelPrice.id).limit(1)) is not None:
        return
    session.add_all(ModelPrice(**p, updated_by=DEFAULT_PRICES_BY) for p in DEFAULT_PRICES)
    session.commit()


def _price_out(p: ModelPrice) -> dict:
    return {
        "model": p.model,
        "input_per_million": p.input_per_million,
        "cached_input_per_million": p.cached_input_per_million,
        "output_per_million": p.output_per_million,
        "updated_by": p.updated_by,
        "updated_at": p.updated_at,
    }


def list_prices(session: Session) -> dict:
    """Every price, plus models in use (the current one, and any already called) that have no price yet."""
    prices = session.scalars(select(ModelPrice).order_by(ModelPrice.model)).all()
    priced = {p.model for p in prices}
    used = set(session.scalars(select(AIUsage.model).distinct()))
    current = llm.model_name() if llm.ai_available() else ""
    missing = sorted(m for m in used | {current} if m and m not in priced)
    return {
        "prices": [_price_out(p) for p in prices],
        "missing": missing,
        "current_model": current,
        "current_provider": llm.provider_name() if llm.ai_available() else "",
    }


def save_price(
    session: Session, model: str, input_per_million: float, cached_input_per_million: float,
    output_per_million: float, updated_by: str,
) -> dict:
    """Add or change a model's price. Only calls made from now on are priced with it, plus older calls
    that had no price at all. Raises PriceError with a friendly message."""
    model, updated_by = model.strip(), updated_by.strip()
    if not model:
        raise PriceError("Please enter the model name, exactly as it appears in the .env file (e.g. gpt-5.4-2).")
    if not updated_by:
        raise PriceError("Please enter your name.")
    if min(input_per_million, cached_input_per_million, output_per_million) < 0:
        raise PriceError("Prices can't be negative.")
    price = session.scalar(select(ModelPrice).where(ModelPrice.model == model))
    if price is None:
        price = ModelPrice(model=model)
        session.add(price)
    price.input_per_million = input_per_million
    price.cached_input_per_million = cached_input_per_million
    price.output_per_million = output_per_million
    price.updated_by = updated_by
    price.updated_at = datetime.now(timezone.utc)
    session.commit()
    return _price_out(price)


# ---------- Usage Analytics numbers ----------


def summary(session: Session, date_from: date | None = None, date_to: date | None = None) -> dict:
    s = _rows(session, "usage_summary", date_from, date_to)[0]
    reviews = s["reviews"] or 0
    return {
        **s,
        "total_tokens": s["input_tokens"] + s["output_tokens"],
        "cost_per_review": s["review_cost"] / reviews if reviews and s["review_cost"] is not None else None,
    }


def _period_start(day: date, period: str) -> date:
    return day - timedelta(days=day.weekday()) if period == "week" else day.replace(day=1)


def _next_period(start: date, period: str) -> date:
    if period == "week":
        return start + timedelta(days=7)
    return (start.replace(day=28) + timedelta(days=4)).replace(day=1)  # first day of next month


def trend(session: Session, period: str = "week", date_from: date | None = None, date_to: date | None = None) -> list[dict]:
    """Calls, tokens and cost per week (starting Monday) or per month. Periods with no usage are
    included, from the start of the date range (or the first usage) to its end (or the last usage)."""
    if period not in PERIODS:
        raise ValueError(f"period must be week or month, not '{period}'")
    buckets: dict[date, dict] = {}
    for row in _rows(session, "usage_per_day", date_from, date_to):
        start = _period_start(date.fromisoformat(str(row["day"])), period)
        b = buckets.setdefault(start, {"calls": 0, "tokens": 0, "cost": 0.0})
        b["calls"] += row["calls"]
        b["tokens"] += row["tokens"] or 0
        b["cost"] += row["cost"] or 0
    if not buckets:
        return []
    # Show the whole chosen range (but not future periods), and never cut off a period that has usage.
    first = min(_period_start(date_from, period), min(buckets)) if date_from else min(buckets)
    last = max(_period_start(min(date_to, date.today()), period), max(buckets)) if date_to else max(buckets)
    result = []
    start = first
    while start <= last:
        b = buckets.get(start, {"calls": 0, "tokens": 0, "cost": 0.0})
        result.append({"period_start": start.isoformat(), **b, "cost": round(b["cost"], 6)})
        start = _next_period(start, period)
    return result


def by_model(session: Session, date_from: date | None = None, date_to: date | None = None) -> list[dict]:
    return [{**r, "has_price": bool(r["has_price"])} for r in _rows(session, "usage_by_model", date_from, date_to)]


def by_purpose(session: Session, date_from: date | None = None, date_to: date | None = None) -> list[dict]:
    return _rows(session, "usage_by_purpose", date_from, date_to)
