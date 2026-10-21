"""Running a review: AI (or demo) judges each rule, code scores it, results are saved.

Reviews run in the background after an upload. The page polls GET /api/reviews/{id}.
"""

import logging
from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DocumentVersion, Review, RuleResult, Suggestion
from app.schemas import (
    ReviewDetail,
    Rule,
    RuleRef,
    RuleResultOut,
    SuggestionOut,
    VersionComparison,
)
from app.services import demo_reviewer, llm
from app.services.scoring import calculate_score

logger = logging.getLogger(__name__)

INTERRUPTED_MESSAGE = "This review was interrupted because the server restarted. Click Re-run review to try again."
UNEXPECTED_MESSAGE = "Something went wrong while reviewing this document. Click Re-run review to try again."


def run_review(review_id: int, session_factory: Callable[[], Session]) -> None:
    """Run one queued review from start to finish. Never raises: failures are saved on the review."""
    with session_factory() as session:
        review = session.get(Review, review_id)
        if review is None or review.status != "queued":
            return
        review.status = "processing"
        review.started_at = datetime.now(timezone.utc)
        session.commit()

        version = review.document_version
        rulebook = review.rulebook_version
        rules = [Rule(**r) for r in rulebook.rules_json]
        try:
            output, model_name, prompt_version = llm.evaluate_rules(
                version.extracted_text, rules, version.document.document_type.display_name
            )
            statuses = {result.rule_id: result.status for result in output.results}
            result = calculate_score(rules, statuses, rulebook.pass_threshold)
        except llm.AIError as e:
            _fail(session, review, str(e))
            return
        except Exception:
            logger.exception("Review %s failed unexpectedly", review_id)  # logs the error, not the document
            _fail(session, review, UNEXPECTED_MESSAGE)
            return

        judgements = {j.rule_id: j for j in output.results}
        for rule in rules:  # saved in rulebook order
            judgement = judgements[rule.id]
            rule_result = RuleResult(
                rule_id=rule.id,
                rule_title=rule.title,
                weight=rule.weight,
                critical=rule.critical,
                status=judgement.status,
                points_earned=result.points_earned[rule.id],
                points_possible=result.points_possible[rule.id],
                evidence=judgement.evidence,
                location=judgement.location,
                explanation=judgement.explanation,
            )
            rule_result.suggestions = [
                Suggestion(
                    type=s.type,
                    location=s.location,
                    current_text=s.current_text,
                    proposed_text=s.proposed_text,
                    rationale=s.rationale,
                )
                for s in judgement.suggestions
            ]
            review.rule_results.append(rule_result)

        review.score = result.score
        review.passed = result.passed
        review.critical_failure = bool(result.critical_failures)
        review.model_name = model_name
        review.prompt_version = prompt_version
        review.status = "complete"
        review.completed_at = datetime.now(timezone.utc)
        version.document.updated_at = review.completed_at
        session.commit()


def _fail(session: Session, review: Review, message: str) -> None:
    review.status = "error"
    review.error_message = message
    review.completed_at = datetime.now(timezone.utc)
    session.commit()


def mark_interrupted_reviews(session: Session) -> int:
    """On startup: reviews left queued or processing by a restart can't finish, so mark them as errors."""
    stuck = session.scalars(select(Review).where(Review.status.in_(["queued", "processing"]))).all()
    for review in stuck:
        _fail(session, review, INTERRUPTED_MESSAGE)
    return len(stuck)


def rerun_review(session: Session, review_id: int) -> Review | None:
    """Queue a fresh review of the same document version, using the latest rulebook."""
    old = session.get(Review, review_id)
    if old is None:
        return None
    doc_type = old.document_version.document.document_type
    review = Review(document_version=old.document_version, rulebook_version=doc_type.latest_version)
    session.add(review)
    session.commit()
    return review


def update_suggestion_state(session: Session, suggestion_id: int, user_state: str) -> Suggestion | None:
    suggestion = session.get(Suggestion, suggestion_id)
    if suggestion is None:
        return None
    suggestion.user_state = user_state
    session.commit()
    return suggestion


# ---------- Reading results ----------


def latest_complete_review(version: DocumentVersion) -> Review | None:
    complete = [r for r in version.reviews if r.status == "complete"]
    return complete[-1] if complete else None


def _comparison(review: Review) -> VersionComparison | None:
    """How this review compares with the previous version of the same document."""
    version = review.document_version
    if review.status != "complete" or version.version_number == 1:
        return None
    previous_version = next(
        (v for v in version.document.versions if v.version_number == version.version_number - 1), None
    )
    previous = latest_complete_review(previous_version) if previous_version else None
    if previous is None:
        return None
    before = {r.rule_id: r.status for r in previous.rule_results}
    newly_met = [
        RuleRef(rule_id=r.rule_id, title=r.rule_title)
        for r in review.rule_results
        if r.status == "met" and r.rule_id in before and before[r.rule_id] != "met"
    ]
    newly_not_met = [
        RuleRef(rule_id=r.rule_id, title=r.rule_title)
        for r in review.rule_results
        if r.status == "not_met" and r.rule_id in before and before[r.rule_id] != "not_met"
    ]
    return VersionComparison(
        previous_version_number=previous_version.version_number,
        previous_review_id=previous.id,
        previous_score=previous.score,
        score_change=review.score - previous.score,
        rules_updated=review.rulebook_version_id != previous.rulebook_version_id,
        newly_met=newly_met,
        newly_not_met=newly_not_met,
    )


def get_review(session: Session, review_id: int) -> ReviewDetail | None:
    review = session.get(Review, review_id)
    if review is None:
        return None
    version = review.document_version
    document = version.document
    rulebook = review.rulebook_version

    return ReviewDetail(
        id=review.id,
        status=review.status,
        error_message=review.error_message,
        is_demo=review.prompt_version == demo_reviewer.PROMPT_VERSION if review.status == "complete" else not llm.ai_available(),
        score=review.score,
        passed=review.passed,
        pass_threshold=rulebook.pass_threshold,
        critical_failures=[
            RuleRef(rule_id=r.rule_id, title=r.rule_title)
            for r in review.rule_results
            if r.critical and r.status == "not_met"
        ],
        model_name=review.model_name,
        prompt_version=review.prompt_version,
        rulebook_version=rulebook.version_number,
        rule_count=len(rulebook.rules_json),
        created_at=review.created_at,
        completed_at=review.completed_at,
        document_id=document.id,
        document_title=document.title,
        document_type_key=document.document_type.key,
        document_type_name=document.document_type.display_name,
        project_name=document.project_name,
        uploaded_by=document.uploaded_by,
        version_number=version.version_number,
        latest_version_number=document.versions[-1].version_number,
        original_filename=version.original_filename,
        rules=[
            RuleResultOut(
                rule_id=r.rule_id,
                title=r.rule_title,
                weight=r.weight,
                critical=r.critical,
                status=r.status,
                points_earned=r.points_earned,
                points_possible=r.points_possible,
                evidence=r.evidence,
                location=r.location,
                explanation=r.explanation,
                suggestions=[
                    SuggestionOut(
                        id=s.id,
                        type=s.type,
                        location=s.location,
                        current_text=s.current_text,
                        proposed_text=s.proposed_text,
                        rationale=s.rationale,
                        user_state=s.user_state,
                    )
                    for s in r.suggestions
                ],
            )
            for r in review.rule_results
        ],
        comparison=_comparison(review),
    )
