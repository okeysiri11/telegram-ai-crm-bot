"""Release Platform Suite facade — Sprint 21.8 / v6.0.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_release.facade import ReleaseLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ReleasePlatformSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = ReleaseLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations()

    def bootstrap(self) -> dict[str, Any]:
        self.library = ReleaseLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("erl_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.erl_bootstraps.save(bid, record)
        cid = _id("erl_cert")
        self.store.erl_certifications.save(
            cid, {"certification_id": cid, **full["certification"], "certified_at": _now()}
        )
        mid = _id("erl_mig")
        self.store.erl_migrations.save(mid, {"migration_id": mid, **full["migration"], "planned_at": _now()})
        did = _id("erl_dr")
        self.store.erl_disaster_recovery.save(
            did, {"dr_id": did, **full["disaster_recovery"], "validated_at": _now()}
        )
        nid = _id("erl_notes")
        self.store.erl_release_notes.save(
            nid, {"notes_id": nid, **full["release_notes"], "generated_at": _now()}
        )
        vid = _id("erl_val")
        self.store.erl_validations.save(
            vid, {"validation_id": vid, **full["validation"], "validated_at": _now()}
        )
        aid = _id("erl_appr")
        self.store.erl_approvals.save(aid, {"approval_id": aid, **full["approval"], "approved_at": _now()})
        man_id = _id("erl_man")
        self.store.erl_manifests.save(
            man_id, {"manifest_id": man_id, **full["manifest"], "published_at": _now()}
        )
        record["certification_id"] = cid
        record["manifest_id"] = man_id
        record["approval_id"] = aid
        record["notes_id"] = nid
        self.store.erl_bootstraps.save(bid, record)
        return record

    def certify(self) -> dict[str, Any]:
        result = self.library.certification.certify()
        cid = _id("erl_cert")
        record = {"certification_id": cid, **result, "certified_at": _now()}
        self.store.erl_certifications.save(cid, record)
        return record

    def validate_production(self) -> dict[str, Any]:
        result = self.library.validation.run()
        vid = _id("erl_val")
        record = {"validation_id": vid, **result, "validated_at": _now()}
        self.store.erl_validations.save(vid, record)
        return record

    def migrate(self) -> dict[str, Any]:
        result = self.library.migration.plan()
        mid = _id("erl_mig")
        record = {"migration_id": mid, **result, "planned_at": _now()}
        self.store.erl_migrations.save(mid, record)
        return record

    def disaster_recovery(self) -> dict[str, Any]:
        result = self.library.disaster_recovery.validate()
        did = _id("erl_dr")
        record = {"dr_id": did, **result, "validated_at": _now()}
        self.store.erl_disaster_recovery.save(did, record)
        return record

    def release_notes(self) -> dict[str, Any]:
        items = self.store.erl_release_notes.list_all()
        if items:
            return items[-1]
        result = self.library.release_notes.generate()
        nid = _id("erl_notes")
        record = {"notes_id": nid, **result, "generated_at": _now()}
        self.store.erl_release_notes.save(nid, record)
        return record

    def approve(
        self,
        *,
        architecture: bool = True,
        quality: bool = True,
        security: bool = True,
        documentation: bool = True,
    ) -> dict[str, Any]:
        if not all(isinstance(x, bool) for x in (architecture, quality, security, documentation)):
            raise ValidationError("approval flags must be boolean")
        result = self.library.approve(
            architecture=architecture,
            quality=quality,
            security=security,
            documentation=documentation,
        )
        aid = _id("erl_appr")
        record = {"approval_id": aid, **result, "approved_at": _now()}
        self.store.erl_approvals.save(aid, record)
        if result["approved"]:
            man = self.library.manifest.publish(approval=result)
            man_id = _id("erl_man")
            self.store.erl_manifests.save(
                man_id, {"manifest_id": man_id, **man, "published_at": _now()}
            )
            record["manifest_id"] = man_id
            self.store.erl_approvals.save(aid, record)
        return record

    def production_manifest(self) -> dict[str, Any]:
        items = self.store.erl_manifests.list_all()
        if not items:
            raise NotFoundError("production manifest not found; bootstrap or approve first")
        return items[-1]

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.erl_bootstraps.list_all()),
            "certifications": len(self.store.erl_certifications.list_all()),
            "manifests": len(self.store.erl_manifests.list_all()),
            "approvals": len(self.store.erl_approvals.list_all()),
        }


release_platform = ReleasePlatformSuite()
