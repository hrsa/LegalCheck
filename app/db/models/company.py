from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base_class import BaseSoftDelete


class Company(BaseSoftDelete):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    registration_number: Mapped[str | None] = mapped_column(String, nullable=True)
    country: Mapped[str | None] = mapped_column(String, nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    invite_code: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                          default=lambda: datetime.now(timezone.utc)
                                                          )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),
                                                                 default=lambda: datetime.now(
                                                                     timezone.utc),
                                                                 onupdate=lambda: datetime.now(
                                                                     timezone.utc))

    documents: Mapped[list["Document"]] = relationship("Document", back_populates="company", cascade="delete")
    policies: Mapped[list["Policy"]] = relationship("Policy", back_populates="company", cascade="delete")
    users: Mapped["User"] = relationship("User", back_populates="company", cascade="delete")
    checklists: Mapped[list["Checklist"]] = relationship("Checklist", back_populates="company", cascade="delete")
