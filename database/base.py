# SQLAlchemy declarative base for PostgreSQL models.

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared metadata base for Alembic autogenerate and async sessions."""
