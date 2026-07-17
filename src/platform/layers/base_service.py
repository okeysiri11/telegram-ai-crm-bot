# Base service — owns database session lifecycle for business operations.

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session

T = TypeVar("T")


class BaseService:
    """Service base class. Only services (and repositories they call) open DB sessions."""

    @staticmethod
    @asynccontextmanager
    async def session() -> AsyncIterator[AsyncSession]:
        async with get_session() as db:
            yield db

    @classmethod
    async def with_session(cls, fn: Callable[[AsyncSession], Any]) -> Any:
        async with cls.session() as db:
            return await fn(db)
