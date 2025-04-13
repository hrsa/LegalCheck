from datetime import datetime, timezone

from sqlalchemy import Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.api.v1.schemas.rule import RuleType, Severity
from app.db.base_class import Base


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    policy_id: Mapped[int] = mapped_column(Integer, ForeignKey("policies.id"))
    rule_type: Mapped[RuleType] = mapped_column(String)  # conflict, risk, requirement
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[Severity] = mapped_column(String)  # high, medium, low
    keywords: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    policy: Mapped["Policy"] = relationship("Policy", back_populates="rules")
    embedding: Mapped["Embedding"] = relationship(
        "Embedding",
        primaryjoin="and_(foreign(Embedding.content_id)==PolicyRule.id, Embedding.content_type=='rule')",
        uselist=False,
        viewonly=True
    )

