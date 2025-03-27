import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base_class import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    registration_number: Mapped[str] = mapped_column(String, index=True)
    country: Mapped[str] = mapped_column(String)
    address: Mapped[str] = mapped_column(String)
    risk_score: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True),
                                                          default=lambda: datetime.datetime.now(datetime.timezone.utc)
                                                          )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True),
                                                                 default=lambda: datetime.datetime.now(
                                                                     datetime.timezone.utc),
                                                                 onupdate=lambda: datetime.datetime.now(
                                                                     datetime.timezone.utc))

    documents: Mapped[list["Document"]] = relationship("Document", back_populates="company")
    policies: Mapped[list["Policy"]] = relationship("Policy", back_populates="company")
    users: Mapped["User"] = relationship("User", back_populates="company")
