"""Extension SDK Suite — Sprint 25.0 / v8.0.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_enterprise_extension_sdk.facade import ExtensionSDKLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ExtensionSDKSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = ExtensionSDKLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = ExtensionSDKLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("ees_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.ees_bootstraps.save(bid, record)
        ext = full["extension"]
        self.store.ees_extensions.save(ext["extension_id"], {**ext, "created_at": _now()})
        for key, attr, prefix in (
            ("verification", "ees_verifications", "ees_ver"),
            ("listing", "ees_marketplace", "ees_mkt"),
            ("installed", "ees_installs", "ees_ins"),
            ("permission_decision", "ees_permissions", "ees_perm"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        record["extension_id"] = ext["extension_id"]
        self.store.ees_bootstraps.save(bid, record)
        return record

    def register(self, **kwargs: Any) -> dict[str, Any]:
        try:
            ext = self.library.registry.register(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.ees_extensions.save(ext["extension_id"], {**ext, "created_at": _now()})
        return ext

    def scaffold(self, *, extension_type: str, name: str) -> dict[str, Any]:
        try:
            return self.library.sdk.scaffold(extension_type=extension_type, name=name)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

    def request_permissions(self, *, extension_id: str, scopes: list[str]) -> dict[str, Any]:
        try:
            result = self.library.permissions.request(extension_id=extension_id, scopes=scopes)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("ees_perm")
        record = {"permission_id": rid, **result, "created_at": _now()}
        self.store.ees_permissions.save(rid, record)
        return record

    def decide_permissions(self, **kwargs: Any) -> dict[str, Any]:
        try:
            result = self.library.permissions.decide(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("ees_perm")
        record = {"permission_id": rid, **result, "created_at": _now()}
        self.store.ees_permissions.save(rid, record)
        return record

    def verify(self, *, extension_id: str, fail_check: str | None = None) -> dict[str, Any]:
        ext = self.store.ees_extensions.get(extension_id)
        if not ext:
            raise NotFoundError(f"extension not found: {extension_id}")
        result = self.library.verification.run(extension=ext, fail_check=fail_check)
        if result["passed"]:
            updated = {**ext, "signature": result["signature"], "signed": True}
            updated = self.library.registry.set_status(updated, status="verified")
            self.store.ees_extensions.save(extension_id, updated)
        rid = _id("ees_ver")
        record = {"verification_id": rid, **result, "created_at": _now()}
        self.store.ees_verifications.save(rid, record)
        return record

    def transition(self, *, extension_id: str, to_status: str) -> dict[str, Any]:
        ext = self.store.ees_extensions.get(extension_id)
        if not ext:
            raise NotFoundError(f"extension not found: {extension_id}")
        try:
            updated = self.library.lifecycle.transition(extension=ext, to_status=to_status)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.ees_extensions.save(extension_id, {**updated, "updated_at": _now()})
        return updated

    def install(self, *, extension_id: str, allow_unsigned: bool = False) -> dict[str, Any]:
        ext = self.store.ees_extensions.get(extension_id)
        if not ext:
            raise NotFoundError(f"extension not found: {extension_id}")
        try:
            result = self.library.loader.install(extension=ext, allow_unsigned=allow_unsigned)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        updated = self.library.registry.set_status(ext, status="installed")
        self.store.ees_extensions.save(extension_id, updated)
        rid = _id("ees_ins")
        record = {"install_id": rid, **result, "created_at": _now()}
        self.store.ees_installs.save(rid, record)
        return record

    def update(self, *, extension_id: str, to_version: str) -> dict[str, Any]:
        try:
            result = self.library.loader.update(extension_id=extension_id, to_version=to_version)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        ext = self.store.ees_extensions.get(extension_id)
        if ext:
            updated = {**ext, "version": to_version, "status": "updated"}
            self.store.ees_extensions.save(extension_id, updated)
        return result

    def uninstall(self, *, extension_id: str) -> dict[str, Any]:
        try:
            result = self.library.loader.uninstall(extension_id=extension_id)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        ext = self.store.ees_extensions.get(extension_id)
        if ext:
            updated = self.library.registry.set_status(ext, status="archived")
            self.store.ees_extensions.save(extension_id, updated)
        return result

    def rollback(self, *, extension_id: str, to_version: str) -> dict[str, Any]:
        try:
            result = self.library.loader.rollback(extension_id=extension_id, to_version=to_version)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        ext = self.store.ees_extensions.get(extension_id)
        if ext:
            updated = {**ext, "version": to_version, "status": "installed"}
            self.store.ees_extensions.save(extension_id, updated)
        return result

    def marketplace_list(self, *, extension_id: str, category: str) -> dict[str, Any]:
        ext = self.store.ees_extensions.get(extension_id)
        if not ext:
            raise NotFoundError(f"extension not found: {extension_id}")
        try:
            listing = self.library.marketplace.list_extension(extension=ext, category=category)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        if ext.get("status") == "verified":
            updated = self.library.registry.set_status(ext, status="published")
            self.store.ees_extensions.save(extension_id, updated)
        rid = _id("ees_mkt")
        record = {"marketplace_id": rid, **listing, "created_at": _now()}
        self.store.ees_marketplace.save(rid, record)
        return record

    def marketplace_catalog(self) -> dict[str, Any]:
        catalog = self.library.marketplace.catalog()
        catalog["listings"] = self.store.ees_marketplace.list_all()
        return catalog

    def public_call(self, *, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            return self.library.public_api.call(method=method, payload=payload)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

    def list_extensions(self) -> dict[str, Any]:
        items = self.store.ees_extensions.list_all()
        return {"extensions": items, "count": len(items)}

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.ees_bootstraps.list_all()),
            "extensions": len(self.store.ees_extensions.list_all()),
            "marketplace_listings": len(self.store.ees_marketplace.list_all()),
            "modifies_enterprise_core": False,
        }


extension_sdk = ExtensionSDKSuite()
