"""Schema / DTO registry — Sprint 21.3."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SchemaRegistry:
    def __init__(self) -> None:
        self._schemas: dict[str, list[dict[str, Any]]] = {}

    def publish(self, *, name: str, schema: dict[str, Any], version: int | None = None) -> dict[str, Any]:
        if not name or not schema:
            raise ValueError("name and schema are required")
        versions = self._schemas.setdefault(name, [])
        ver = version or (len(versions) + 1)
        if any(v["version"] == ver for v in versions):
            raise ValueError(f"schema version already exists: {name}@{ver}")
        record = {
            "schema_id": f"sch_{uuid.uuid4().hex[:12]}",
            "name": name,
            "version": ver,
            "schema": deepcopy(schema),
            "status": "active",
            "published_at": _now(),
        }
        versions.append(record)
        return record

    def get(self, name: str, version: int | None = None) -> dict[str, Any]:
        versions = self._schemas.get(name) or []
        if not versions:
            raise KeyError(f"schema not found: {name}")
        if version is None:
            return versions[-1]
        for item in versions:
            if item["version"] == version:
                return item
        raise KeyError(f"schema version not found: {name}@{version}")

    def list_versions(self, name: str) -> list[dict[str, Any]]:
        return list(self._schemas.get(name) or [])

    def rollback(self, name: str, version: int) -> dict[str, Any]:
        target = self.get(name, version)
        # republish as new active version with same schema content
        return self.publish(name=name, schema=target["schema"])

    def compatibility(self, name: str, candidate: dict[str, Any]) -> dict[str, Any]:
        current = self.get(name)
        current_props = set((current["schema"].get("properties") or {}).keys())
        candidate_props = set((candidate.get("properties") or {}).keys())
        removed = sorted(current_props - candidate_props)
        return {
            "compatible": len(removed) == 0,
            "removed_fields": removed,
            "added_fields": sorted(candidate_props - current_props),
            "current_version": current["version"],
        }

    def status(self) -> dict[str, Any]:
        return {
            "schemas": len(self._schemas),
            "versions": sum(len(v) for v in self._schemas.values()),
        }


class DtoRegistry:
    def __init__(self) -> None:
        self._dtos: dict[str, dict[str, Any]] = {}

    def register(self, *, name: str, domain: str, fields: list[str], version: int = 1) -> dict[str, Any]:
        if not name or not domain:
            raise ValueError("name and domain are required")
        key = f"{domain}.{name}"
        record = {
            "dto_id": f"dto_{uuid.uuid4().hex[:12]}",
            "key": key,
            "name": name,
            "domain": domain,
            "fields": list(fields),
            "version": version,
            "registered_at": _now(),
        }
        self._dtos[key] = record
        return record

    def list_all(self) -> list[dict[str, Any]]:
        return list(self._dtos.values())

    def status(self) -> dict[str, Any]:
        return {"dtos": len(self._dtos)}
