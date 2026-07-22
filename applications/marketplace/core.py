"""Marketplace Core — registries, versioning, deps, install/update/rollback, licenses (Sprint 12.1)."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.marketplace.config import DEFAULT_CONFIG
from applications.marketplace.shared.exceptions import CompatibilityError, NotFoundError, ValidationError
from applications.marketplace.shared.store import MarketplaceStore, marketplace_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


PACKAGE_KINDS = ("plugin", "connector", "workflow", "application", "agent", "pack")


class MarketplaceManager:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.categories = list(DEFAULT_CONFIG.categories)

    def publish_package(
        self,
        *,
        name: str,
        kind: str,
        category: str = "custom_enterprise",
        version: str = "1.0.0",
        publisher: str = "",
        dependencies: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        private: bool = False,
        org_id: str = "",
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("package name required")
        if kind not in PACKAGE_KINDS:
            raise ValidationError(f"kind must be one of {PACKAGE_KINDS}")
        if category not in self.categories:
            raise ValidationError(f"category must be one of {self.categories}")
        pid = f"pkg_{uuid.uuid4().hex[:12]}"
        item = {
            "package_id": pid,
            "name": name,
            "kind": kind,
            "category": category,
            "version": version,
            "publisher": publisher or "anonymous",
            "dependencies": list(dependencies or []),
            "metadata": dict(metadata or {}),
            "private": private,
            "org_id": org_id,
            "status": "published",
            "downloads": 0,
            "rating_avg": 0.0,
            "rating_count": 0,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.packages.save(pid, item)
        self.store.versions.save(
            f"{pid}:{version}",
            {"package_id": pid, "version": version, "created_at": _now(), "changelog": metadata.get("changelog", "") if metadata else ""},
        )
        # Mirror into kind-specific registry
        self._mirror_kind(item)
        return item

    def _mirror_kind(self, item: dict[str, Any]) -> None:
        kind = item["kind"]
        bucket = {
            "plugin": self.store.plugins,
            "connector": self.store.connectors,
            "workflow": self.store.workflows,
            "application": self.store.applications,
            "agent": self.store.agents,
        }.get(kind)
        if bucket is not None:
            bucket.save(item["package_id"], item)

    def get_package(self, package_id: str) -> dict[str, Any]:
        item = self.store.packages.get(package_id)
        if item is None:
            raise NotFoundError("package", package_id)
        return item

    def list_packages(self, *, kind: str | None = None, category: str | None = None, org_id: str | None = None) -> list[dict[str, Any]]:
        items = self.store.packages.list_all()
        if kind:
            items = [i for i in items if i.get("kind") == kind]
        if category:
            items = [i for i in items if i.get("category") == category]
        if org_id is not None:
            items = [i for i in items if i.get("org_id") == org_id or (not org_id and not i.get("private"))]
        return items

    def package_registry(self) -> dict[str, Any]:
        return {"registry": "package", "packages": self.list_packages(), "count": len(self.store.packages.list_all())}

    def plugin_registry(self) -> dict[str, Any]:
        return {"registry": "plugin", "items": self.store.plugins.list_all(), "count": len(self.store.plugins.list_all())}

    def connector_registry(self) -> dict[str, Any]:
        return {"registry": "connector", "items": self.store.connectors.list_all(), "count": len(self.store.connectors.list_all())}

    def workflow_registry(self) -> dict[str, Any]:
        return {"registry": "workflow", "items": self.store.workflows.list_all(), "count": len(self.store.workflows.list_all())}

    def application_registry(self) -> dict[str, Any]:
        return {"registry": "application", "items": self.store.applications.list_all(), "count": len(self.store.applications.list_all())}

    def agent_registry(self) -> dict[str, Any]:
        return {"registry": "agent", "items": self.store.agents.list_all(), "count": len(self.store.agents.list_all())}

    def check_compatibility(self, package_id: str, *, platform_version: str = "3.0.0") -> dict[str, Any]:
        pkg = self.get_package(package_id)
        deps = pkg.get("dependencies") or []
        missing = [d for d in deps if not any(p.get("name") == d or p.get("package_id") == d for p in self.store.packages.list_all())]
        # Simple semver gate: marketplace requires platform v3
        compatible = platform_version.startswith("3.") and not missing
        result = {
            "package_id": package_id,
            "platform_version": platform_version,
            "compatible": compatible,
            "missing_dependencies": missing,
            "checked_at": _now(),
        }
        if not compatible and missing:
            result["reason"] = "missing_dependencies"
        elif not compatible:
            result["reason"] = "platform_incompatible"
        return result

    def resolve_dependencies(self, package_id: str) -> dict[str, Any]:
        pkg = self.get_package(package_id)
        resolved = []
        for dep in pkg.get("dependencies") or []:
            match = next((p for p in self.store.packages.list_all() if p.get("name") == dep or p.get("package_id") == dep), None)
            resolved.append({"dependency": dep, "found": match is not None, "package_id": match.get("package_id") if match else None})
        return {"package_id": package_id, "dependencies": resolved, "ok": all(r["found"] for r in resolved)}

    def install(self, package_id: str, *, org_id: str = "", user_id: str = "") -> dict[str, Any]:
        pkg = self.get_package(package_id)
        compat = self.check_compatibility(package_id)
        if not compat["compatible"]:
            raise CompatibilityError(compat.get("reason", "incompatible"))
        deps = self.resolve_dependencies(package_id)
        if not deps["ok"]:
            raise CompatibilityError("unresolved_dependencies")
        iid = f"inst_{uuid.uuid4().hex[:12]}"
        installation = {
            "installation_id": iid,
            "package_id": package_id,
            "name": pkg["name"],
            "kind": pkg["kind"],
            "version": pkg["version"],
            "org_id": org_id,
            "user_id": user_id,
            "status": "installed",
            "installed_at": _now(),
        }
        self.store.installations.save(iid, installation)
        pkg["downloads"] = int(pkg.get("downloads", 0)) + 1
        pkg["updated_at"] = _now()
        self.store.packages.save(package_id, pkg)
        self._mirror_kind(pkg)
        did = f"dl_{uuid.uuid4().hex[:10]}"
        self.store.downloads.save(did, {"download_id": did, "package_id": package_id, "at": _now()})
        return installation

    def update(self, installation_id: str, *, to_version: str) -> dict[str, Any]:
        inst = self.store.installations.get(installation_id)
        if inst is None:
            raise NotFoundError("installation", installation_id)
        pkg = self.get_package(inst["package_id"])
        prev = inst["version"]
        inst["previous_version"] = prev
        inst["version"] = to_version
        inst["status"] = "updated"
        inst["updated_at"] = _now()
        self.store.installations.save(installation_id, inst)
        self.store.versions.save(
            f"{pkg['package_id']}:{to_version}",
            {"package_id": pkg["package_id"], "version": to_version, "created_at": _now(), "from_version": prev},
        )
        pkg["version"] = to_version
        pkg["updated_at"] = _now()
        self.store.packages.save(pkg["package_id"], pkg)
        self._mirror_kind(pkg)
        return inst

    def rollback(self, installation_id: str) -> dict[str, Any]:
        inst = self.store.installations.get(installation_id)
        if inst is None:
            raise NotFoundError("installation", installation_id)
        prev = inst.get("previous_version")
        if not prev:
            raise ValidationError("no previous version to rollback")
        inst["version"] = prev
        inst["status"] = "rolled_back"
        inst["rolled_back_at"] = _now()
        self.store.installations.save(installation_id, inst)
        return inst

    def issue_license(self, package_id: str, *, org_id: str, seats: int = 1, plan: str = "enterprise") -> dict[str, Any]:
        self.get_package(package_id)
        lid = f"lic_{uuid.uuid4().hex[:12]}"
        key = hashlib.sha256(f"{package_id}:{org_id}:{_now()}".encode()).hexdigest()[:24]
        license_row = {
            "license_id": lid,
            "package_id": package_id,
            "org_id": org_id,
            "seats": seats,
            "plan": plan,
            "license_key": key,
            "status": "active",
            "issued_at": _now(),
        }
        self.store.licenses.save(lid, license_row)
        return license_row

    def rate(self, package_id: str, *, score: float, reviewer: str = "", comment: str = "") -> dict[str, Any]:
        pkg = self.get_package(package_id)
        if score < 1 or score > 5:
            raise ValidationError("score must be 1..5")
        rid = f"rate_{uuid.uuid4().hex[:10]}"
        rating = {"rating_id": rid, "package_id": package_id, "score": score, "reviewer": reviewer, "comment": comment, "at": _now()}
        self.store.ratings.save(rid, rating)
        ratings = [r for r in self.store.ratings.list_all() if r.get("package_id") == package_id]
        pkg["rating_count"] = len(ratings)
        pkg["rating_avg"] = round(sum(r["score"] for r in ratings) / len(ratings), 2)
        self.store.packages.save(package_id, pkg)
        self._mirror_kind(pkg)
        return rating

    def list_installations(self) -> list[dict[str, Any]]:
        return self.store.installations.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "marketplace_core": "1.0",
            "packages": len(self.store.packages.list_all()),
            "installations": len(self.store.installations.list_all()),
            "categories": self.categories,
            "ready": True,
        }


marketplace_manager = MarketplaceManager()
