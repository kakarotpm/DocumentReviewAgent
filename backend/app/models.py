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
