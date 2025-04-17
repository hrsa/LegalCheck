from sqlalchemy.orm import DeclarativeBase

from app.db.soft_delete import SoftDeleteMixin

class Base(DeclarativeBase):
    pass

class BaseSoftDelete(SoftDeleteMixin, Base):
    __abstract__ = True
    pass
