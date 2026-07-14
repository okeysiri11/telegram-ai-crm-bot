# Tenant entry registry repository.

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.tenant_entry_registry import OwnerVerticalNote, TenantEntryLink


class TenantEntryLinkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[TenantEntryLink]:
        result = await self._session.execute(
            select(TenantEntryLink)
            .where(TenantEntryLink.is_active.is_(True))
            .order_by(TenantEntryLink.sort_order, TenantEntryLink.code)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[TenantEntryLink]:
        result = await self._session.execute(
            select(TenantEntryLink).order_by(TenantEntryLink.sort_order, TenantEntryLink.code)
        )
        return list(result.scalars().all())

    async def get_by_code(self, code: str) -> TenantEntryLink | None:
        result = await self._session.execute(
            select(TenantEntryLink).where(TenantEntryLink.code == code)
        )
        return result.scalar_one_or_none()

    async def upsert_seed(self, *, code: str, **fields) -> TenantEntryLink:
        row = await self.get_by_code(code)
        if row is None:
            row = TenantEntryLink(code=code, **fields)
            self._session.add(row)
        else:
            for key, value in fields.items():
                setattr(row, key, value)
        await self._session.flush()
        return row


class OwnerVerticalNoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_vertical(self, vertical: str) -> list[OwnerVerticalNote]:
        result = await self._session.execute(
            select(OwnerVerticalNote)
            .where(OwnerVerticalNote.vertical == vertical)
            .order_by(OwnerVerticalNote.title)
        )
        return list(result.scalars().all())

    async def list_all_grouped(self) -> dict[str, list[OwnerVerticalNote]]:
        result = await self._session.execute(
            select(OwnerVerticalNote).order_by(
                OwnerVerticalNote.vertical, OwnerVerticalNote.title
            )
        )
        grouped: dict[str, list[OwnerVerticalNote]] = {}
        for row in result.scalars().all():
            grouped.setdefault(row.vertical, []).append(row)
        return grouped

    async def get_by_id(self, note_id: uuid.UUID) -> OwnerVerticalNote | None:
        result = await self._session.execute(
            select(OwnerVerticalNote).where(OwnerVerticalNote.id == note_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        tenant_code: str,
        vertical: str,
        title: str,
        content: str = "",
    ) -> OwnerVerticalNote:
        row = OwnerVerticalNote(
            tenant_code=tenant_code,
            vertical=vertical,
            title=title,
            content=content,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def update_content(self, note_id: uuid.UUID, content: str) -> OwnerVerticalNote | None:
        row = await self.get_by_id(note_id)
        if row is None:
            return None
        row.content = content
        await self._session.flush()
        return row
