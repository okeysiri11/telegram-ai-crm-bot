# ConfigurationService — centralized platform settings with versioning and cache.

from __future__ import annotations

import logging
from typing import Any

from database.session import get_session
from events.configuration_events import ConfigurationChangedEvent
from events.event_bus import publish
from platform_configuration.config_cache import config_cache
from platform_configuration.config_provider import config_provider
from platform_configuration.config_repository import ConfigRepository
from platform_configuration.config_schema import section_for_key
from platform_configuration.config_validator import ConfigValidationError, ConfigValidator

logger = logging.getLogger(__name__)

_SYSTEM_ACTORS = frozenset({"system", "bootstrap", "import"})


class ConfigurationPermissionError(PermissionError):
    pass


class ConfigurationService:
    @staticmethod
    async def _check_write_permission(
        changed_by: str | None,
        *,
        actor_telegram_id: int | None = None,
    ) -> None:
        if changed_by in _SYSTEM_ACTORS:
            return
        permission = config_provider.get(
            "security.config_write_permission",
            "platform.config.write",
        )
        if actor_telegram_id is not None:
            from services.pg_platform_permissions_engine import PlatformPermissionsEngineV1

            allowed = await PlatformPermissionsEngineV1.user_has_permission(
                actor_telegram_id,
                str(permission),
            )
            if not allowed:
                raise ConfigurationPermissionError(
                    f"Missing permission {permission!r} for actor {actor_telegram_id}"
                )
            return
        if changed_by:
            return
        raise ConfigurationPermissionError("Configuration write requires actor or system context")

    @staticmethod
    async def _publish_change(
        *,
        key: str,
        action: str,
        old_value: Any,
        new_value: Any,
        version: int,
        changed_by: str | None,
        reason: str | None,
    ) -> None:
        event = ConfigurationChangedEvent(
            config_key=key,
            action=action,
            section=section_for_key(key),
            old_value=old_value,
            new_value=new_value,
            version=version,
            changed_by=changed_by,
            reason=reason,
        )
        await publish(event)

    @staticmethod
    async def get(key: str, *, use_cache: bool = True) -> Any:
        ConfigValidator.validate_key(key)
        if use_cache:
            cached = await config_cache.get(key)
            if cached is not None:
                return cached.get("value")

        async with get_session() as session:
            repo = ConfigRepository(session)
            entry = await repo.get_entry(key)

        if entry is not None:
            await config_cache.set(key, {"value": entry.value, "version": entry.version})
            return entry.value

        default = config_provider.get(key)
        return default

    @staticmethod
    async def set(
        key: str,
        value: Any,
        *,
        changed_by: str | None = None,
        reason: str | None = None,
        actor_telegram_id: int | None = None,
    ) -> dict[str, Any]:
        await ConfigurationService._check_write_permission(
            changed_by,
            actor_telegram_id=actor_telegram_id,
        )
        validated = ConfigValidator.validate_value(key, value)

        async with get_session() as session:
            repo = ConfigRepository(session)
            entry, history = await repo.upsert(
                key,
                validated,
                changed_by=changed_by,
                reason=reason,
            )

        config_provider.update_key(key, validated)
        await config_cache.set(key, {"value": validated, "version": entry.version})
        await config_cache.invalidate_section(section_for_key(key))

        await ConfigurationService._publish_change(
            key=key,
            action="set",
            old_value=history.old_value,
            new_value=validated,
            version=entry.version,
            changed_by=changed_by,
            reason=reason,
        )
        return ConfigRepository.snapshot(entry)

    @staticmethod
    async def delete(
        key: str,
        *,
        changed_by: str | None = None,
        reason: str | None = None,
        actor_telegram_id: int | None = None,
    ) -> dict[str, Any] | None:
        await ConfigurationService._check_write_permission(
            changed_by,
            actor_telegram_id=actor_telegram_id,
        )
        ConfigValidator.validate_key(key)

        async with get_session() as session:
            repo = ConfigRepository(session)
            existing = await repo.get_entry(key)
            history = await repo.delete_key(key, changed_by=changed_by, reason=reason)

        if history is None:
            return None

        config_provider.remove_key(key)
        await config_cache.delete(key)
        await config_cache.invalidate_section(section_for_key(key))

        await ConfigurationService._publish_change(
            key=key,
            action="delete",
            old_value=history.old_value,
            new_value=None,
            version=history.version,
            changed_by=changed_by,
            reason=reason,
        )
        return ConfigRepository.history_snapshot(history)

    @staticmethod
    async def rollback(
        key: str,
        version: int,
        *,
        changed_by: str | None = None,
        reason: str | None = None,
        actor_telegram_id: int | None = None,
    ) -> dict[str, Any] | None:
        await ConfigurationService._check_write_permission(
            changed_by,
            actor_telegram_id=actor_telegram_id,
        )
        ConfigValidator.validate_key(key)

        async with get_session() as session:
            repo = ConfigRepository(session)
            entry, history = await repo.rollback_to_version(
                key,
                version,
                changed_by=changed_by,
                reason=reason,
            )

        if entry is None or history is None:
            return None

        config_provider.update_key(key, entry.value)
        await config_cache.set(key, {"value": entry.value, "version": entry.version})
        await config_cache.invalidate_section(section_for_key(key))

        await ConfigurationService._publish_change(
            key=key,
            action="rollback",
            old_value=history.old_value,
            new_value=entry.value,
            version=entry.version,
            changed_by=changed_by,
            reason=reason,
        )
        return ConfigRepository.snapshot(entry)

    @staticmethod
    async def validate(payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if payload is None:
            async with get_session() as session:
                repo = ConfigRepository(session)
                entries = await repo.list_entries()
            payload = {row.key: row.value for row in entries}

        validated = ConfigValidator.validate_payload(payload)
        return {"valid": True, "keys": len(validated), "values": validated}

    @staticmethod
    async def export() -> dict[str, Any]:
        async with get_session() as session:
            repo = ConfigRepository(session)
            return await repo.export_all()

    @staticmethod
    async def import_config(
        payload: dict[str, Any],
        *,
        changed_by: str | None = None,
        reason: str | None = None,
        actor_telegram_id: int | None = None,
    ) -> dict[str, Any]:
        await ConfigurationService._check_write_permission(
            changed_by or "import",
            actor_telegram_id=actor_telegram_id,
        )

        entries = payload.get("entries") if isinstance(payload.get("entries"), dict) else payload
        if isinstance(entries, dict):
            ConfigValidator.validate_payload(
                {
                    key: meta["value"] if isinstance(meta, dict) and "value" in meta else meta
                    for key, meta in entries.items()
                }
            )

        async with get_session() as session:
            repo = ConfigRepository(session)
            updated_keys = await repo.import_entries(
                payload,
                changed_by=changed_by or "import",
                reason=reason or "import",
            )

        for key in updated_keys:
            value = await ConfigurationService.get(key, use_cache=False)
            config_provider.update_key(key, value)
            await config_cache.delete(key)

        await config_cache.clear()

        for key in updated_keys:
            await ConfigurationService._publish_change(
                key=key,
                action="import",
                old_value=None,
                new_value=config_provider.get(key),
                version=0,
                changed_by=changed_by or "import",
                reason=reason or "import",
            )

        return {"imported": len(updated_keys), "keys": updated_keys}

    @staticmethod
    async def get_history(key: str, *, limit: int = 50) -> list[dict[str, Any]]:
        async with get_session() as session:
            repo = ConfigRepository(session)
            rows = await repo.get_history(key, limit=limit)
        return [ConfigRepository.history_snapshot(row) for row in rows]

    @staticmethod
    async def bootstrap(*, include_env: bool = True) -> dict[str, Any]:
        from platform_configuration.config_loader import load_runtime_snapshot, seed_platform_configuration

        seed_result = await seed_platform_configuration(include_env=include_env)
        snapshot = seed_result.get("snapshot") or await load_runtime_snapshot()
        config_provider.apply_snapshot(snapshot)
        return seed_result


configuration_service = ConfigurationService()
