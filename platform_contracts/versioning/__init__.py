"""Contract versioning & migration — Sprint 21.3."""

from __future__ import annotations

from typing import Any


class VersionCompatibility:
    def migrate(self, data: dict[str, Any], *, from_version: int, to_version: int) -> dict[str, Any]:
        if from_version > to_version:
            raise ValueError("cannot migrate backwards via migrate(); use rollback on registry")
        out = dict(data)
        out["version"] = to_version
        deprecated = list(out.get("metadata", {}).get("deprecated_fields") or [])
        out.setdefault("metadata", {})
        out["metadata"]["migrated_from"] = from_version
        out["metadata"]["deprecated_fields"] = deprecated
        return out

    def check(self, *, current: int, previous: int, deprecated_fields: list[str] | None = None) -> dict[str, Any]:
        return {
            "current": current,
            "previous": previous,
            "deprecated_fields": list(deprecated_fields or []),
            "backward_compatible": current >= previous,
        }
