# Configuration repository — PostgreSQL persistence with history.

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select

from database.models.platform_configuration import PlatformConfigEntry, PlatformConfigHistory
from platform_configuration.config_schema import section_for_key
from src.platform.layers.base_repository import BaseRepository


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _serialize_value(value: Any) -> Any:
    if isinstance(value, (dict, list, str, int, float, bool)) or value is None:
        return value
    return json.loads(json.dumps(value, default=str))


class ConfigRepository(BaseRepository):
    async def get_entry(self, key: str) -> PlatformConfigEntry | None:
        result = await self.session.execute(
            select(PlatformConfigEntry).where(PlatformConfigEntry.key == key)
        )
        return result.scalar_one_or_none()

    async def list_entries(self, *, section: str | None = None) -> list[PlatformConfigEntry]:
        stmt = select(PlatformConfigEntry).order_by(PlatformConfigEntry.key)
        if section:
            stmt = stmt.where(PlatformConfigEntry.section == section)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert(
        self,
        key: str,
        value: Any,
        *,
        changed_by: str | None = None,
        reason: str | None = None,
        value_type: str = "json",
        description: str | None = None,
    ) -> tuple[PlatformConfigEntry, PlatformConfigHistory]:
        serialized = _serialize_value(value)
        existing = await self.get_entry(key)
        old_value = existing.value if existing else None
        new_version = (existing.version + 1) if existing else 1

        if existing is None:
            row = PlatformConfigEntry(
                key=key,
                section=section_for_key(key),
                value=serialized,
                value_type=value_type,
                version=new_version,
                description=description,
                updated_by=changed_by,
            )
            self.session.add(row)
        else:
            row = existing
            row.value = serialized
            row.value_type = value_type
            row.version = new_version
            row.updated_by = changed_by
            if description is not None:
                row.description = description

        history = PlatformConfigHistory(
            config_key=key,
            version=new_version,
            old_value=old_value,
            new_value=serialized,
            action="set",
            changed_by=changed_by,
            reason=reason,
            changed_at=_utcnow(),
        )
        self.session.add(history)
        await self.session.flush()
        return row, history

    async def delete_key(
        self,
        key: str,
        *,
        changed_by: str | None = None,
        reason: str | None = None,
    ) -> PlatformConfigHistory | None:
        existing = await self.get_entry(key)
        if existing is None:
            return None

        new_version = existing.version + 1
        history = PlatformConfigHistory(
            config_key=key,
            version=new_version,
            old_value=existing.value,
            new_value=None,
            action="delete",
            changed_by=changed_by,
            reason=reason,
            changed_at=_utcnow(),
        )
        self.session.add(history)
        await self.session.execute(
            delete(PlatformConfigEntry).where(PlatformConfigEntry.key == key)
        )
        await self.session.flush()
        return history

    async def get_history(
        self,
        key: str,
        *,
        limit: int = 50,
    ) -> list[PlatformConfigHistory]:
        result = await self.session.execute(
            select(PlatformConfigHistory)
            .where(PlatformConfigHistory.config_key == key)
            .order_by(PlatformConfigHistory.version.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_history_version(
        self,
        key: str,
        version: int,
    ) -> PlatformConfigHistory | None:
        result = await self.session.execute(
            select(PlatformConfigHistory).where(
                PlatformConfigHistory.config_key == key,
                PlatformConfigHistory.version == version,
            )
        )
        return result.scalar_one_or_none()

    async def rollback_to_version(
        self,
        key: str,
        version: int,
        *,
        changed_by: str | None = None,
        reason: str | None = None,
    ) -> tuple[PlatformConfigEntry | None, PlatformConfigHistory | None]:
        target = await self.get_history_version(key, version)
        if target is None:
            return None, None

        restore_value = target.new_value if target.action != "delete" else target.old_value
        if restore_value is None and target.old_value is not None:
            restore_value = target.old_value

        existing = await self.get_entry(key)
        old_value = existing.value if existing else None
        new_version = (existing.version + 1) if existing else version

        if existing is None:
            row = PlatformConfigEntry(
                key=key,
                section=section_for_key(key),
                value=restore_value,
                value_type="json",
                version=new_version,
                updated_by=changed_by,
            )
            self.session.add(row)
        else:
            row = existing
            row.value = restore_value
            row.version = new_version
            row.updated_by = changed_by

        history = PlatformConfigHistory(
            config_key=key,
            version=new_version,
            old_value=old_value,
            new_value=restore_value,
            action="rollback",
            changed_by=changed_by,
            reason=reason or f"rollback_to_v{version}",
            changed_at=_utcnow(),
        )
        self.session.add(history)
        await self.session.flush()
        return row, history

    async def export_all(self) -> dict[str, Any]:
        entries = await self.list_entries()
        return {
            "version": 1,
            "exported_at": _utcnow().isoformat(),
            "entries": {
                row.key: {
                    "value": row.value,
                    "section": row.section,
                    "version": row.version,
                    "value_type": row.value_type,
                }
                for row in entries
            },
        }

    async def import_entries(
        self,
        payload: dict[str, Any],
        *,
        changed_by: str | None = None,
        reason: str | None = None,
    ) -> list[str]:
        entries = payload.get("entries") or payload
        updated_keys: list[str] = []
        if not isinstance(entries, dict):
            return updated_keys

        for key, meta in entries.items():
            if isinstance(meta, dict) and "value" in meta:
                value = meta["value"]
                vtype = meta.get("value_type", "json")
            else:
                value = meta
                vtype = "json"
            await self.upsert(
                key,
                value,
                changed_by=changed_by,
                reason=reason or "import",
                value_type=str(vtype),
            )
            updated_keys.append(key)
        return updated_keys

    @staticmethod
    def snapshot(entry: PlatformConfigEntry) -> dict[str, Any]:
        return {
            "key": entry.key,
            "section": entry.section,
            "value": entry.value,
            "value_type": entry.value_type,
            "version": entry.version,
            "description": entry.description,
            "updated_by": entry.updated_by,
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
        }

    @staticmethod
    def history_snapshot(row: PlatformConfigHistory) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "config_key": row.config_key,
            "version": row.version,
            "old_value": row.old_value,
            "new_value": row.new_value,
            "action": row.action,
            "changed_by": row.changed_by,
            "reason": row.reason,
            "changed_at": row.changed_at.isoformat() if row.changed_at else None,
        }

    async def seed_defaults(self, defaults: dict[str, Any]) -> int:
        seeded = 0
        for key, value in defaults.items():
            existing = await self.get_entry(key)
            if existing is not None:
                continue
            await self.upsert(
                key,
                value,
                changed_by="system",
                reason="initial_seed",
                value_type=type(value).__name__ if value is not None else "json",
            )
            seeded += 1
        return seeded
