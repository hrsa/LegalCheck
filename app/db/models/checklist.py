import datetime

from sqlalchemy import String, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base_class import Base


class Checklist(Base):
    __tablename__ = "checklists"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    company_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True)
    ruleset: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True),
                                                          default=lambda: datetime.datetime.now(datetime.timezone.utc)
                                                          )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True),
                                                                 default=lambda: datetime.datetime.now(
                                                                     datetime.timezone.utc),
                                                                 onupdate=lambda: datetime.datetime.now(
                                                                     datetime.timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="checklists")
    company: Mapped["Company"] = relationship("Company", back_populates="checklists")
    # rules: Mapped[list["PolicyRule"]] = relationship("PolicyRule",
    #                                                  primaryjoin="PolicyRule.id.in_(func.json_array_elements(Checklist.ruleset))",
    #                                                  viewonly=True
    #                                                  )
