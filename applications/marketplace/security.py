"""Marketplace security — verification, signatures, permission/sandbox/dependency scans (Sprint 12.1)."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.marketplace.core import MarketplaceManager, marketplace_manager
from applications.marketplace.shared.store import MarketplaceStore, marketplace_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MarketplaceSecurity:
    def __init__(self, store: MarketplaceStore | None = None, core: MarketplaceManager | None = None) -> None:
        self.store = store or marketplace_store
        self.core = core or marketplace_manager

    def verify_plugin(self, package_id: str) -> dict[str, Any]:
        pkg = self.core.get_package(package_id)
        checks = {
            "has_name": bool(pkg.get("name")),
            "has_version": bool(pkg.get("version")),
            "kind_known": pkg.get("kind") in {"plugin", "connector", "workflow", "application", "agent", "pack"},
            "category_known": pkg.get("category") in self.core.categories,
        }
        passed = all(checks.values())
        return self._save_scan(package_id, "verification", passed, checks)

    def digital_signature(self, package_id: str, *, signer: str = "marketplace") -> dict[str, Any]:
        pkg = self.core.get_package(package_id)
        payload = f"{pkg['package_id']}:{pkg['name']}:{pkg['version']}:{signer}"
        signature = hashlib.sha256(payload.encode()).hexdigest()
        result = {"package_id": package_id, "signer": signer, "signature": signature, "algo": "sha256", "at": _now()}
        meta = pkg.setdefault("metadata", {})
        meta["signature"] = signature
        meta["signer"] = signer
        self.store.packages.save(package_id, pkg)
        return result

    def permission_scanner(self, package_id: str) -> dict[str, Any]:
        pkg = self.core.get_package(package_id)
        perms = list((pkg.get("metadata") or {}).get("permissions") or [])
        risky = [p for p in perms if p in {"shell", "filesystem_write", "network_unrestricted"}]
        passed = not risky
        return self._save_scan(package_id, "permissions", passed, {"permissions": perms, "risky": risky})

    def sandbox_validation(self, package_id: str) -> dict[str, Any]:
        pkg = self.core.get_package(package_id)
        # Structural sandbox gate — no executable payloads in metadata
        meta = pkg.get("metadata") or {}
        unsafe = any(k in meta for k in ("exec", "binary", "shell_script"))
        return self._save_scan(package_id, "sandbox", not unsafe, {"unsafe_keys": unsafe})

    def dependency_validation(self, package_id: str) -> dict[str, Any]:
        resolved = self.core.resolve_dependencies(package_id)
        return self._save_scan(package_id, "dependencies", resolved["ok"], resolved)

    def full_scan(self, package_id: str) -> dict[str, Any]:
        results = [
            self.verify_plugin(package_id),
            self.digital_signature(package_id),
            self.permission_scanner(package_id),
            self.sandbox_validation(package_id),
            self.dependency_validation(package_id),
        ]
        passed = all(r.get("passed", True) for r in results if "passed" in r)
        return {"package_id": package_id, "passed": passed, "scans": results, "at": _now()}

    def _save_scan(self, package_id: str, scan_type: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
        sid = f"scan_{uuid.uuid4().hex[:12]}"
        row = {"scan_id": sid, "package_id": package_id, "scan_type": scan_type, "passed": passed, "details": details, "at": _now()}
        self.store.security_scans.save(sid, row)
        return row

    def status(self) -> dict[str, Any]:
        return {"security": "1.0", "scans": len(self.store.security_scans.list_all()), "ready": True}


marketplace_security = MarketplaceSecurity()
