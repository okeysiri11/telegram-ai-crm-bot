
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

import re


class DependencyManager:
    """Resolve plugin dependencies, versions, conflicts, and compatibility."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def resolve(
        self,
        *,
        plugin_id: str,
        dependencies: list[str] | None = None,
        platform_version: str = "5.4.6-enterprise",
    ) -> dict[str, Any]:
        deps = list(dependencies or [])
        conflicts: list[str] = []
        resolved: list[dict[str, str]] = []
        seen: set[str] = set()
        for dep in deps:
            name, constraint = self._parse(dep)
            if name in seen:
                conflicts.append(f"duplicate dependency: {name}")
                continue
            seen.add(name)
            installed = self.store.sdp_plugins.get(name)
            if installed:
                ver = installed.get("version", "0.0.0")
                if not self._satisfies(ver, constraint):
                    conflicts.append(f"{name}@{ver} does not satisfy {constraint or '*'}")
                else:
                    resolved.append({"name": name, "version": ver, "status": "satisfied"})
            else:
                resolved.append({"name": name, "version": constraint or "*", "status": "pending"})
        rid = _id("sdp_dep")
        record = {
            "resolution_id": rid,
            "plugin_id": plugin_id,
            "platform_version": platform_version,
            "dependencies": deps,
            "resolved": resolved,
            "conflicts": conflicts,
            "compatible": len(conflicts) == 0,
            "at": _now(),
        }
        return self.store.sdp_dependencies.save(rid, record)

    def _parse(self, spec: str) -> tuple[str, str]:
        if "@" in spec:
            name, constraint = spec.split("@", 1)
            return name.strip(), constraint.strip()
        return spec.strip(), ""

    def _satisfies(self, version: str, constraint: str) -> bool:
        if not constraint or constraint in ("*", "latest"):
            return True
        m = re.match(r"^(>=|<=|>|<|==)?\s*([0-9]+(?:\.[0-9]+)*)", constraint)
        if not m:
            return version == constraint
        op, target = m.group(1) or "==", m.group(2)
        va, vb = self._tuple(version), self._tuple(target)
        if op == "==":
            return va == vb
        if op == ">=":
            return va >= vb
        if op == "<=":
            return va <= vb
        if op == ">":
            return va > vb
        if op == "<":
            return va < vb
        return True

    def _tuple(self, version: str) -> tuple[int, ...]:
        parts = re.findall(r"\d+", version.split("-")[0])
        return tuple(int(p) for p in parts) or (0,)

    def status(self) -> dict[str, Any]:
        items = self.store.sdp_dependencies.list_all()
        return {
            "resolutions": len(items),
            "conflicts": sum(1 for i in items if i.get("conflicts")),
        }
