import datetime

from sqlalchemy import ForeignKey, JSON, DateTime, String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.api.v1.schemas.analysis import Conflict, Risk, MissingClause, Suggestion, PaymentTerm
from app.db.base_class import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    company_name: Mapped[str | None] = mapped_column(String, nullable=True)
    conflicts: Mapped[list[Conflict] | None] = mapped_column(JSON, nullable=True)
    risks: Mapped[list[Risk] | None] = mapped_column(JSON, nullable=True)
    missing_clauses: Mapped[list[MissingClause] | None] = mapped_column(JSON, nullable=True)
    suggestions: Mapped[list[Suggestion] | None] = mapped_column(JSON, nullable=True)
    payment_terms: Mapped[list[PaymentTerm] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True),
                                                          default=lambda: datetime.datetime.now(datetime.timezone.utc)
                                                          )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True),
                                                                 default=lambda: datetime.datetime.now(
                                                                     datetime.timezone.utc),
                                                                 onupdate=lambda: datetime.datetime.now(
                                                                     datetime.timezone.utc))

    document: Mapped["Document"] = relationship("Document", back_populates="analysis_results")
