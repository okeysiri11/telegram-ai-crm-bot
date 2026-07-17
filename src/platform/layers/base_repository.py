# Base repository — SQLAlchemy data access only (no business rules).

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """Async repository bound to a single SQLAlchemy session.

    Subclasses implement CRUD and queries. Business rules belong in services.
    """

    __slots__ = ("_session",)

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def session(self) -> AsyncSession:
        return self._session
