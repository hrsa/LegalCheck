from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, JSON

from app.api.v1.schemas.rule import RuleType, Severity
from app.db.base_class import Base
from sqlalchemy.orm import relationship, Mapped, mapped_column
import datetime

from app.db.models import Policy, Embedding


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    policy_id: Mapped[int] = mapped_column(Integer, ForeignKey("policies.id"))
    rule_type: Mapped[RuleType] = mapped_column(String)  # conflict, risk, requirement
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[Severity] = mapped_column(String)  # high, medium, low
    keywords: Mapped[set[str]] = mapped_column(JSON)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc)
)
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc),
                        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    policy: Mapped[Policy] = relationship("Policy", back_populates="rules")
    embedding: Mapped[Embedding | None] = relationship(
        "Embedding",
        primaryjoin="and_(foreign(Embedding.content_id)==PolicyRule.id, Embedding.content_type=='rule')",
        uselist=False,
        viewonly=True
    )

