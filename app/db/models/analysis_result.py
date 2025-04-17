from datetime import datetime, timezone

from sqlalchemy import ForeignKey, JSON, DateTime, String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.api.v1.schemas.analysis import Conflict, Risk, MissingClause, Suggestion, PaymentTerm
from app.db.base_class import BaseSoftDelete


class AnalysisResult(BaseSoftDelete):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    checklist_id: Mapped[int] = mapped_column(ForeignKey("checklists.id"), nullable=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    company_name: Mapped[str | None] = mapped_column(String, nullable=True)
    conflicts: Mapped[list[Conflict] | None] = mapped_column(JSON, nullable=True)
    risks: Mapped[list[Risk] | None] = mapped_column(JSON, nullable=True)
    missing_clauses: Mapped[list[MissingClause] | None] = mapped_column(JSON, nullable=True)
    suggestions: Mapped[list[Suggestion] | None] = mapped_column(JSON, nullable=True)
    payment_terms: Mapped[list[PaymentTerm] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                          default=lambda: datetime.now(timezone.utc)
                                                          )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),
                                                                 default=lambda: datetime.now(
                                                                     timezone.utc),
                                                                 onupdate=lambda: datetime.now(
                                                                     timezone.utc))

    document: Mapped["Document"] = relationship("Document", back_populates="analysis_results")
    checklist: Mapped["Checklist"] = relationship("Checklist", back_populates="analysis_results")
