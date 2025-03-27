from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, JSON

from app.api.v1.schemas.policy import PolicyType
from app.db.base_class import Base
from sqlalchemy.orm import relationship, Mapped, mapped_column
import datetime


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(Text)
    policy_type: Mapped[PolicyType] = mapped_column(String)  # company, industry, standard
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    company_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True),
                                                          default=lambda: datetime.datetime.now(datetime.timezone.utc)
                                                          )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True),
                                                                 default=lambda: datetime.datetime.now(
                                                                     datetime.timezone.utc),
                                                                 onupdate=lambda: datetime.datetime.now(
                                                                     datetime.timezone.utc))

    company: Mapped["Company"] = relationship("Company", back_populates="policies")
    rules: Mapped[list["PolicyRule"]] = relationship("PolicyRule", back_populates="policy")
    embedding: Mapped["Embedding"] = relationship("Embedding",
                                                  primaryjoin="and_(foreign(Embedding.content_id)==Policy.id, Embedding.content_type=='policy')",
                                                  uselist=False, viewonly=True)
