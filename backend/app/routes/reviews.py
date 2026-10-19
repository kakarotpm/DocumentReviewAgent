"""API endpoints for review results and suggestions."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session, get_session_factory
from app.schemas import ReviewDetail, SuggestionOut, SuggestionStateUpdate
from app.services import review_engine

router = APIRouter(tags=["Reviews"])


@router.get("/api/reviews/{review_id}", response_model=ReviewDetail)
def get_review(review_id: int, session: Session = Depends(get_session)):
    """A review's status and, once complete, its full results."""
    detail = review_engine.get_review(session, review_id)
    if detail is None:
        raise HTTPException(404, f"No review with ID {review_id}.")
    return detail


@router.post("/api/reviews/{review_id}/rerun", response_model=ReviewDetail, status_code=201)
def rerun_review(
    review_id: int,
    background: BackgroundTasks,
    session: Session = Depends(get_session),
    session_factory=Depends(get_session_factory),
):
    """Review the same document version again (with the latest rules). Returns the new review."""
    review = review_engine.rerun_review(session, review_id)
    if review is None:
        raise HTTPException(404, f"No review with ID {review_id}.")
    background.add_task(review_engine.run_review, review.id, session_factory)
    return review_engine.get_review(session, review.id)


@router.patch("/api/suggestions/{suggestion_id}", response_model=SuggestionOut)
def update_suggestion(suggestion_id: int, update: SuggestionStateUpdate, session: Session = Depends(get_session)):
    """Mark a suggestion as open, done or dismissed."""
    suggestion = review_engine.update_suggestion_state(session, suggestion_id, update.user_state)
    if suggestion is None:
        raise HTTPException(404, f"No suggestion with ID {suggestion_id}.")
    return SuggestionOut.model_validate(suggestion, from_attributes=True)
