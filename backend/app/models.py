"""Database tables."""

from datetime import datetime, timezone

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow():
    return datetime.now(timezone.utc)


class DocumentType(Base):
    """A kind of document we can review (BRD, FRD, ... or a custom type)."""

    __tablename__ = "document_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(50), unique=True)
    display_name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(default="")
    is_builtin: Mapped[bool] = mapped_column(default=False)
    # Unsaved custom types are kept (so revised versions still work) but hidden from pickers.
    is_listed: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    versions: Mapped[list["RulebookVersion"]] = relationship(
        back_populates="document_type", order_by="RulebookVersion.version_number"
    )

    @property
    def latest_version(self) -> "RulebookVersion":
        return self.versions[-1]


class RulebookVersion(Base):
    """One saved version of a document type's rules. Never edited after it's created."""

    __tablename__ = "rulebook_versions"
    __table_args__ = (UniqueConstraint("document_type_id", "version_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    document_type_id: Mapped[int] = mapped_column(ForeignKey("document_types.id"))
    version_number: Mapped[int]
    pass_threshold: Mapped[int] = mapped_column(default=80)
    rules_json: Mapped[list] = mapped_column(JSON)
    changed_by: Mapped[str] = mapped_column(String(200))
    change_note: Mapped[str] = mapped_column(default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    document_type: Mapped[DocumentType] = relationship(back_populates="versions")


class Document(Base):
    """An uploaded document. Each upload of a revised file adds a DocumentVersion."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    document_type_id: Mapped[int] = mapped_column(ForeignKey("document_types.id"))
    project_name: Mapped[str] = mapped_column(String(200), default="")
    uploaded_by: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    document_type: Mapped[DocumentType] = relationship()
    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document", order_by="DocumentVersion.version_number"
    )


class DocumentVersion(Base):
    """One uploaded file. Only its extracted text is kept; the file itself is never stored."""

    __tablename__ = "document_versions"
    __table_args__ = (UniqueConstraint("document_id", "version_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    version_number: Mapped[int]
    original_filename: Mapped[str] = mapped_column(String(300))
    file_type: Mapped[str] = mapped_column(String(10))
    extracted_text: Mapped[str]
    uploaded_at: Mapped[datetime] = mapped_column(default=utcnow)

    document: Mapped[Document] = relationship(back_populates="versions")
    reviews: Mapped[list["Review"]] = relationship(back_populates="document_version", order_by="Review.id")


class Review(Base):
    """One AI review of a document version against a specific rulebook version."""

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_version_id: Mapped[int] = mapped_column(ForeignKey("document_versions.id"))
    # The exact (never-changing) rules used, so later rulebook edits don't alter this result.
    rulebook_version_id: Mapped[int] = mapped_column(ForeignKey("rulebook_versions.id"))
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued / processing / complete / error
    score: Mapped[int | None]
    passed: Mapped[bool | None]
    critical_failure: Mapped[bool | None]
    model_name: Mapped[str | None] = mapped_column(String(100))
    prompt_version: Mapped[str | None] = mapped_column(String(50))
    error_message: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]

    document_version: Mapped[DocumentVersion] = relationship(back_populates="reviews")
    rulebook_version: Mapped[RulebookVersion] = relationship()
    rule_results: Mapped[list["RuleResult"]] = relationship(back_populates="review", order_by="RuleResult.id")


class RuleResult(Base):
    """The AI's judgement on one rule in a review, plus the points the code awarded."""

    __tablename__ = "rule_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"))
    rule_id: Mapped[str] = mapped_column(String(20))
    rule_title: Mapped[str] = mapped_column(String(300))
    category: Mapped[str] = mapped_column(String(100))
    weight: Mapped[str] = mapped_column(String(10))  # high / medium / low
    critical: Mapped[bool]
    status: Mapped[str] = mapped_column(String(20))  # met / partially_met / not_met
    points_earned: Mapped[float]
    points_possible: Mapped[int]
    evidence: Mapped[str] = mapped_column(default="")
    location: Mapped[str] = mapped_column(default="")
    explanation: Mapped[str] = mapped_column(default="")

    review: Mapped[Review] = relationship(back_populates="rule_results")
    suggestions: Mapped[list["Suggestion"]] = relationship(back_populates="rule_result", order_by="Suggestion.id")


class Suggestion(Base):
    """A specific fix for the analyst: add, change or delete some content."""

    __tablename__ = "suggestions"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_result_id: Mapped[int] = mapped_column(ForeignKey("rule_results.id"))
    type: Mapped[str] = mapped_column(String(10))  # add / change / delete
    location: Mapped[str] = mapped_column(default="")
    current_text: Mapped[str | None]
    proposed_text: Mapped[str | None]
    rationale: Mapped[str] = mapped_column(default="")
    user_state: Mapped[str] = mapped_column(String(20), default="open")  # open / done / dismissed

    rule_result: Mapped[RuleResult] = relationship(back_populates="suggestions")
