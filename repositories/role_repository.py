# Permission Engine — role repository.

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.role import EngineRoleCode, Role


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_role(
        self,
        *,
        code: str,
        name: str | None = None,
        description: str | None = None,
        **extra: Any,
    ) -> Role:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if code not in {r.value for r in EngineRoleCode}:
            raise ValueError(f"Invalid role code: {code}")

        existing = await self.get_role(code=code)
        if existing is not None:
            return existing

        role = Role(
            code=code,
            name=name or code.replace("_", " ").title(),
            description=description,
        )
        self._session.add(role)
        await self._session.flush()
        return role

    async def get_role(
        self,
        role_id: uuid.UUID | None = None,
        *,
        code: str | None = None,
    ) -> Role | None:
        if role_id is not None:
            result = await self._session.execute(
                select(Role).where(Role.id == role_id)
            )
            return result.scalar_one_or_none()
        if code is not None:
            result = await self._session.execute(
                select(Role).where(Role.code == code)
            )
            return result.scalar_one_or_none()
        raise ValueError("role_id or code is required")

    async def list_roles(self) -> list[Role]:
        result = await self._session.execute(
            select(Role).order_by(Role.code.asc())
        )
        return list(result.scalars().all())
