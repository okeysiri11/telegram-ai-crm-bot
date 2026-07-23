
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

import hashlib

from applications.enterprise_hub.developer_platform.models import PACKAGE_ACTIONS


class PackageManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def install(
        self,
        *,
        package_id: str,
        name: str,
        version: str = "1.0.0",
        plugin_id: str | None = None,
        checksum: str | None = None,
    ) -> dict[str, Any]:
        if not package_id or not name:
            raise ValidationError("package_id and name are required")
        digest = checksum or hashlib.sha256(f"{package_id}:{version}".encode()).hexdigest()
        pid = plugin_id or package_id
        record = {
            "package_id": package_id,
            "plugin_id": pid,
            "name": name,
            "version": version,
            "checksum": digest,
            "integrity_ok": True,
            "installed_at": _now(),
            "status": "installed",
        }
        self.store.sdp_packages.save(package_id, record)
        return self._action(package_id, "install", {"version": version, "checksum": digest})

    def uninstall(self, *, package_id: str) -> dict[str, Any]:
        pkg = self._get(package_id)
        pkg["status"] = "uninstalled"
        pkg["uninstalled_at"] = _now()
        self.store.sdp_packages.save(package_id, pkg)
        return self._action(package_id, "uninstall")

    def update(self, *, package_id: str, version: str) -> dict[str, Any]:
        pkg = self._get(package_id)
        prev = pkg.get("version")
        pkg["previous_version"] = prev
        pkg["version"] = version
        pkg["checksum"] = hashlib.sha256(f"{package_id}:{version}".encode()).hexdigest()
        pkg["updated_at"] = _now()
        pkg["status"] = "installed"
        self.store.sdp_packages.save(package_id, pkg)
        return self._action(package_id, "update", {"from": prev, "to": version})

    def rollback(self, *, package_id: str) -> dict[str, Any]:
        pkg = self._get(package_id)
        prev = pkg.get("previous_version")
        if not prev:
            raise ValidationError("no previous version to rollback")
        current = pkg.get("version")
        pkg["version"] = prev
        pkg["previous_version"] = current
        pkg["status"] = "rolled_back"
        pkg["updated_at"] = _now()
        self.store.sdp_packages.save(package_id, pkg)
        return self._action(package_id, "rollback", {"to": prev})

    def verify_integrity(self, *, package_id: str) -> dict[str, Any]:
        pkg = self._get(package_id)
        expected = hashlib.sha256(f"{package_id}:{pkg.get('version')}".encode()).hexdigest()
        ok = pkg.get("checksum") == expected
        return self._action(package_id, "verify", {"integrity_ok": ok, "checksum": pkg.get("checksum")})

    def _get(self, package_id: str) -> dict[str, Any]:
        pkg = self.store.sdp_packages.get(package_id)
        if not pkg:
            raise NotFoundError(f"package not found: {package_id}")
        return pkg

    def _action(self, package_id: str, action: str, extra: dict | None = None) -> dict[str, Any]:
        if action not in PACKAGE_ACTIONS:
            raise ValidationError(f"invalid action: {action}")
        aid = _id("sdp_pkg")
        record = {
            "action_id": aid,
            "package_id": package_id,
            "action": action,
            "at": _now(),
            **(extra or {}),
        }
        return self.store.sdp_package_actions.save(aid, record)

    def status(self) -> dict[str, Any]:
        pkgs = self.store.sdp_packages.list_all()
        return {
            "packages": len(pkgs),
            "installed": sum(1 for p in pkgs if p.get("status") == "installed"),
            "actions": len(self.store.sdp_package_actions.list_all()),
        }
