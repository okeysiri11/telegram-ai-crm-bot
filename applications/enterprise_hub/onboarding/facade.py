"""Enterprise Onboarding Suite facade — Sprint 22.9 / v6.10.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_enterprise_onboarding.facade import EnterpriseOnboardingLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EnterpriseOnboardingSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = EnterpriseOnboardingLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = EnterpriseOnboardingLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("eon_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.eon_bootstraps.save(bid, record)
        wid = _id("eon_wiz")
        self.store.eon_wizards.save(wid, {"wizard_id": wid, **full["wizard"], "created_at": _now()})
        iid = _id("eon_imp")
        self.store.eon_imports.save(iid, {"import_id": iid, **full["import"], "created_at": _now()})
        vid = _id("eon_val")
        self.store.eon_validations.save(vid, {"validation_id": vid, **full["validation"], "created_at": _now()})
        aid = _id("eon_ai")
        self.store.eon_assistant.save(aid, {"assistant_id": aid, **full["assistant"], "created_at": _now()})
        cid = _id("eon_cfg")
        self.store.eon_configs.save(cid, {"config_id": cid, **full["config"], "created_at": _now()})
        rid = _id("eon_rdy")
        self.store.eon_readiness.save(rid, {"readiness_id": rid, **full["readiness"], "created_at": _now()})
        gid = _id("eon_live")
        self.store.eon_go_live.save(gid, {"go_live_id": gid, **full["go_live"], "created_at": _now()})
        record["wizard_id"] = wid
        record["import_id"] = iid
        record["go_live_id"] = gid
        self.store.eon_bootstraps.save(bid, record)
        return record

    def start_wizard(self, **kwargs: Any) -> dict[str, Any]:
        try:
            session = self.library.wizard.start(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        wid = _id("eon_wiz")
        record = {"wizard_id": wid, **session, "created_at": _now()}
        self.store.eon_wizards.save(wid, record)
        return record

    def advance_wizard(self, *, wizard_id: str, step_data: dict[str, Any] | None = None) -> dict[str, Any]:
        session = self.store.eon_wizards.get(wizard_id)
        if not session:
            raise NotFoundError(f"wizard not found: {wizard_id}")
        try:
            updated = self.library.wizard.advance(session, step_data=step_data)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        record = {**session, **updated, "updated_at": _now()}
        self.store.eon_wizards.save(wizard_id, record)
        return record

    def import_data(self, **kwargs: Any) -> dict[str, Any]:
        try:
            staged = self.library.import_center.ingest(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        iid = _id("eon_imp")
        record = {"import_id": iid, **staged, "created_at": _now()}
        self.store.eon_imports.save(iid, record)
        return record

    def validate_import(self, *, import_id: str | None = None, entity: str = "", rows: list | None = None) -> dict[str, Any]:
        if import_id:
            staged = self.store.eon_imports.get(import_id)
            if not staged:
                raise NotFoundError(f"import not found: {import_id}")
            entity = staged.get("entity") or entity
            rows = staged.get("rows") or []
        report = self.library.validation.validate(entity=entity, rows=list(rows or []))
        vid = _id("eon_val")
        record = {"validation_id": vid, "import_id": import_id, **report, "created_at": _now()}
        self.store.eon_validations.save(vid, record)
        return record

    def migration_advise(self, **kwargs: Any) -> dict[str, Any]:
        advice = self.library.migration_assistant.advise(**kwargs)
        aid = _id("eon_ai")
        record = {"assistant_id": aid, **advice, "created_at": _now()}
        self.store.eon_assistant.save(aid, record)
        return record

    def apply_initial_config(self, *, wizard_id: str) -> dict[str, Any]:
        wizard = self.store.eon_wizards.get(wizard_id)
        if not wizard:
            raise NotFoundError(f"wizard not found: {wizard_id}")
        imports = self.store.eon_imports.list_all()
        # activate platform modules via existing suites (no logic duplication)
        activations: dict[str, Any] = {}
        try:
            from applications.enterprise_hub import enterprise_hub

            if hasattr(enterprise_hub, "communications_hub"):
                activations["communications_hub"] = True
            if hasattr(enterprise_hub, "ai_business_advisor"):
                activations["ai_business_advisor"] = True
            if hasattr(enterprise_hub, "ai_marketing_os"):
                activations["ai_marketing_os"] = True
            if hasattr(enterprise_hub, "product_intelligence"):
                activations["product_intelligence"] = True
            if hasattr(enterprise_hub, "beauty_os") and wizard.get("industry") == "beauty":
                activations["beauty_os"] = True
            if hasattr(enterprise_hub, "commerce_core"):
                activations["commerce_core"] = True
        except Exception:
            pass
        config = self.library.initial_config.apply(wizard=wizard, imports=imports)
        config["activations"] = activations
        cid = _id("eon_cfg")
        record = {"config_id": cid, "wizard_id": wizard_id, **config, "created_at": _now()}
        self.store.eon_configs.save(cid, record)
        return record

    def analyze_readiness(self, *, wizard_id: str) -> dict[str, Any]:
        wizard = self.store.eon_wizards.get(wizard_id)
        if not wizard:
            raise NotFoundError(f"wizard not found: {wizard_id}")
        imports = self.store.eon_imports.list_all()
        configs = [c for c in self.store.eon_configs.list_all() if c.get("wizard_id") == wizard_id]
        config = configs[-1] if configs else {}
        result = self.library.readiness.analyze(
            wizard=wizard,
            imports=imports,
            config=config,
            security_ok=True,
            integrations_ok=True,
        )
        rid = _id("eon_rdy")
        record = {"readiness_id": rid, "wizard_id": wizard_id, **result, "created_at": _now()}
        self.store.eon_readiness.save(rid, record)
        return record

    def go_live(self, *, wizard_id: str, completed: dict[str, bool] | None = None) -> dict[str, Any]:
        wizard = self.store.eon_wizards.get(wizard_id)
        if not wizard:
            raise NotFoundError(f"wizard not found: {wizard_id}")
        checklist = self.library.go_live.evaluate(completed=completed)
        gid = _id("eon_live")
        record = {
            "go_live_id": gid,
            "wizard_id": wizard_id,
            **checklist,
            "created_at": _now(),
        }
        self.store.eon_go_live.save(gid, record)
        if checklist["passed"]:
            wizard = {**wizard, "company_status": "Active", "go_live_at": _now()}
            self.store.eon_wizards.save(wizard_id, wizard)
            record["wizard"] = {"wizard_id": wizard_id, "company_status": "Active"}
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.eon_bootstraps.list_all()),
            "wizards": len(self.store.eon_wizards.list_all()),
            "imports": len(self.store.eon_imports.list_all()),
            "go_lives": len(self.store.eon_go_live.list_all()),
        }


enterprise_onboarding = EnterpriseOnboardingSuite()
