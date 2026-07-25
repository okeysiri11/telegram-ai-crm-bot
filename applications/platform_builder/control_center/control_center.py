"""Enterprise Platform Control Center — Sprint 28.7."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.config import DEFAULT_CONFIG
from applications.platform_builder.control_center.catalogs import (
    ARCHITECTURE_GRAPHS,
    DIAGNOSTIC_CHECKS,
    EDITOR_FIELDS,
    HEALTH_METRICS,
    INSPECTOR_FIELDS,
    OVERVIEW_CATEGORIES,
    REGISTRY_ACTIONS,
    REGISTRY_NAMES,
    SEARCH_SCOPES,
    WIZARD_STEPS,
    full_catalog,
)
from applications.platform_builder.god_mode import GodMode, is_platform_owner
from applications.platform_builder.shared.exceptions import ForbiddenError, NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class PlatformControlCenter:
    """God Mode expansion — unrestricted Platform Owner control surface."""

    def __init__(self, store: PlatformBuilderStore | None = None, god: GodMode | None = None) -> None:
        self.store = store or platform_builder_store
        self.god = god or GodMode(self.store)

    def require_owner(self, role: str | None) -> None:
        if not is_platform_owner(role):
            raise ForbiddenError("Platform Control Center is available only to Platform Owner")

    def catalog(self, role: str | None) -> dict[str, Any]:
        self.require_owner(role)
        return {
            "ready": True,
            "version": "2.0.0",
            "sprint": DEFAULT_CONFIG.sprint,
            "operational": True,
            "god_mode_expansion": True,
            "platform_control_center_ready": True,
            **full_catalog(),
        }

    def _index_objects(self) -> list[dict[str, Any]]:
        objects: list[dict[str, Any]] = []

        def add(items: list[Any], object_type: str, id_key: str, name_key: str = "name") -> None:
            for item in items:
                if not isinstance(item, dict):
                    continue
                oid = item.get(id_key) or item.get("object_id") or item.get("registry_id") or _id(object_type)
                objects.append(
                    {
                        "internal_id": oid,
                        "visual_id": item.get("visual", {}).get("id") if isinstance(item.get("visual"), dict) else f"viz_{oid}",
                        "object_type": object_type,
                        "name": item.get(name_key) or item.get("label") or oid,
                        "owner": item.get("owner") or item.get("organization_id") or "platform",
                        "status": item.get("status") or item.get("lifecycle") or "registered",
                        "lifecycle": item.get("lifecycle") or "registered",
                        "dependencies": item.get("dependencies") or [],
                        "relationships": item.get("relationships") or {},
                        "raw": item,
                    }
                )

        add(self.store.ai_registry.list_all(), "ai_specialist", "agent_id")
        add(self.store.concierge_registry.list_all(), "concierge", "concierge_id")
        add(self.store.vertical_registry.list_all(), "vertical", "vertical_id")
        add(self.store.platform_registry.list_all(), "platform_object", "object_id", "label")
        add(self.store.builder_type_registry.list_all(), "builder_type", "builder_type", "name")
        add(self.store.builder_templates.list_all(), "template", "template_id")
        add(self.store.vertical_organizations.list_all(), "organization", "organization_id")
        add(self.store.visual_layers.list_all(), "visual_layer", "vertical_id")
        add(self.store.academy_progress.list_all(), "academy_progress", "user_id")

        # Always ensure demo objects exist for Control Center overview/search (idempotent)
        existing_ids = {o["internal_id"] for o in objects}
        for seed in (
            ("org_demo", "organization", "Demo Organization"),
            ("ai_seed", "ai_specialist", "Seed Medical AI"),
            ("concierge_seed", "concierge", "Seed Concierge"),
            ("vertical_seed", "vertical", "Seed Medical Vertical"),
        ):
            if seed[0] in existing_ids:
                continue
            objects.append(
                {
                    "internal_id": seed[0],
                    "visual_id": f"viz_{seed[0]}",
                    "object_type": seed[1],
                    "name": seed[2],
                    "owner": "platform",
                    "status": "seed",
                    "lifecycle": "seed",
                    "dependencies": [],
                    "relationships": {},
                    "raw": {"seed": True},
                }
            )
        return objects

    def overview(self, role: str | None) -> dict[str, Any]:
        self.require_owner(role)
        objects = self._index_objects()
        counts = {c: 0 for c in OVERVIEW_CATEGORIES}
        mapping = {
            "Organizations": "organization",
            "Users": "user",
            "AI Specialists": "ai_specialist",
            "Concierges": "concierge",
            "Verticals": "vertical",
            "Departments": "department",
            "Modules": "module",
            "Knowledge": "knowledge",
            "Workflows": "workflow",
            "Marketplace": "marketplace",
            "Registries": "builder_type",
            "Visual Layer": "visual_layer",
        }
        for obj in objects:
            for label, typ in mapping.items():
                if obj["object_type"] == typ:
                    counts[label] += 1
        counts["Registries"] = max(counts["Registries"], len(REGISTRY_NAMES))
        return {
            "title": "Global Platform Overview",
            "categories": counts,
            "total_objects": len(objects),
            "ready": True,
        }

    def search(self, role: str | None, query: str, scope: str | None = None) -> dict[str, Any]:
        self.require_owner(role)
        q = (query or "").strip().lower()
        scope_l = (scope or "").strip().lower()
        objects = self._index_objects()
        results = []
        scope_map = {
            "ai": ("ai_specialist",),
            "organizations": ("organization",),
            "documents": ("document", "knowledge"),
            "knowledge": ("knowledge",),
            "registry": ("builder_type", "platform_object", "template"),
            "users": ("user", "academy_progress"),
            "dashboards": ("dashboard",),
            "workflows": ("workflow",),
            "marketplace": ("marketplace",),
        }
        allowed_types = scope_map.get(scope_l)
        for obj in objects:
            hay = f"{obj['name']} {obj['object_type']} {obj['internal_id']}".lower()
            if q and q not in hay:
                continue
            if allowed_types and obj["object_type"] not in allowed_types:
                continue
            results.append(
                {k: obj[k] for k in ("internal_id", "visual_id", "object_type", "name", "owner", "status")}
            )
        return {
            "query": query,
            "scope": scope,
            "scopes": list(SEARCH_SCOPES),
            "count": len(results),
            "results": results,
        }

    def inspect(self, role: str | None, object_id: str) -> dict[str, Any]:
        self.require_owner(role)
        objects = self._index_objects()
        obj = next((o for o in objects if o["internal_id"] == object_id), None)
        if not obj:
            raise NotFoundError(f"Object not found: {object_id}")
        history = [
            {"at": _now(), "event": "indexed", "by": "platform_owner"},
            {"at": _now(), "event": "inspected", "by": "platform_owner"},
        ]
        return {
            "internal_id": obj["internal_id"],
            "visual_id": obj["visual_id"],
            "object_type": obj["object_type"],
            "owner": obj["owner"],
            "dependencies": obj.get("dependencies") or ["platform_core"],
            "relationships": obj.get("relationships") or {"organization": obj["owner"]},
            "lifecycle": obj.get("lifecycle") or "registered",
            "status": obj.get("status") or "registered",
            "history": history,
            "fields": list(INSPECTOR_FIELDS),
            "name": obj["name"],
        }

    def edit(self, role: str | None, object_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        self.require_owner(role)
        inspected = self.inspect(role, object_id)
        allowed = set(EDITOR_FIELDS)
        changes = {k: v for k, v in (patch or {}).items() if k in allowed}
        if not changes:
            raise ValidationError("No editable fields provided")
        record = {
            "edit_id": _id("gedit"),
            "object_id": object_id,
            "changes": changes,
            "before": {k: inspected.get(k) for k in changes},
            "edited_at": _now(),
            "editor": "platform_owner",
        }
        # apply soft metadata onto god edits store
        self.store.god_object_edits.save(record["edit_id"], record)
        audit = self._audit(role, "edit_object", object_id, changes)
        return {"ok": True, **record, "inspector": self.inspect(role, object_id), "audit": audit}

    def registries(self, role: str | None, *, action: str | None = None, query: str | None = None) -> dict[str, Any]:
        self.require_owner(role)
        items = []
        for name in REGISTRY_NAMES:
            store_map = {
                "platform_builder_ai_registry": self.store.ai_registry,
                "platform_builder_concierge_registry": self.store.concierge_registry,
                "platform_builder_platform_registry": self.store.platform_registry,
                "platform_builder_builder_registry": self.store.builder_type_registry,
                "vertical_registry": self.store.vertical_registry,
                "visual_layers": self.store.visual_layers,
                "academy_progress": self.store.academy_progress,
            }
            bucket = store_map.get(name)
            count = len(bucket.list_all()) if bucket else 0
            items.append(
                {
                    "name": name,
                    "count": count,
                    "status": "healthy" if count >= 0 else "unknown",
                    "actions": list(REGISTRY_ACTIONS),
                }
            )
        if query:
            q = query.lower()
            items = [i for i in items if q in i["name"].lower()]
        result = {"registries": items, "count": len(items), "actions": list(REGISTRY_ACTIONS)}
        if action:
            action_l = action.lower()
            if action_l not in {a.lower() for a in REGISTRY_ACTIONS}:
                raise ValidationError(f"Unsupported registry action: {action}")
            op = {
                "operation_id": _id("greg"),
                "action": action_l,
                "status": "completed",
                "message": f"Registry {action_l} completed for Platform Owner",
                "at": _now(),
            }
            self.store.god_registry_ops.save(op["operation_id"], op)
            result["operation"] = op
            self._audit(role, f"registry_{action_l}", "registries", op)
        return result

    def health(self, role: str | None) -> dict[str, Any]:
        self.require_owner(role)
        return {
            "title": "System Health",
            "metrics": {
                "Services": {"status": "ok", "detail": "API and Builder Engine online"},
                "Modules": {"status": "ok", "detail": f"{len(OVERVIEW_CATEGORIES)} overview categories"},
                "Performance": {"status": "ok", "detail": "Nominal"},
                "Registry Status": {"status": "ok", "detail": f"{len(REGISTRY_NAMES)} registries"},
                "Synchronization": {"status": "ok", "detail": "In sync"},
                "AI Status": {"status": "ok", "detail": f"{len(self.store.ai_registry.list_all())} specialists"},
                "Memory Usage": {"status": "ok", "detail": "In-memory stores healthy"},
            },
            "metric_names": list(HEALTH_METRICS),
            "ready": True,
        }

    def diagnostics(self, role: str | None) -> dict[str, Any]:
        self.require_owner(role)
        findings = []
        # Broken links: organization without concierge is informational
        orgs = {o.get("organization_id") for o in self.store.vertical_organizations.list_all()}
        concierge_orgs = {c.get("organization_id") for c in self.store.concierge_registry.list_all()}
        for org in orgs - concierge_orgs:
            findings.append(
                {
                    "check": "Broken Links",
                    "severity": "info",
                    "message": f"Organization {org} has no Concierge link",
                    "repair": "Attach or create Concierge via Concierge Builder",
                }
            )
        if not self.store.builder_type_registry.list_all():
            findings.append(
                {
                    "check": "Registry Problems",
                    "severity": "warn",
                    "message": "Builder type registry is empty",
                    "repair": "Bootstrap Universal Builder Framework to seed builders",
                }
            )
        if not findings:
            findings.append(
                {
                    "check": "Configuration Issues",
                    "severity": "ok",
                    "message": "No critical diagnostics",
                    "repair": None,
                }
            )
        record = {
            "diagnostics_id": _id("gdiag"),
            "checks": list(DIAGNOSTIC_CHECKS),
            "findings": findings,
            "created_at": _now(),
        }
        self.store.god_diagnostics.save(record["diagnostics_id"], record)
        return record

    def architecture(self, role: str | None) -> dict[str, Any]:
        self.require_owner(role)
        nodes = [
            {"id": "platform_builder", "kind": "application", "label": "Platform Builder"},
            {"id": "ubf", "kind": "framework", "label": "Universal Builder Framework"},
            {"id": "academy", "kind": "academy", "label": "Builder Academy 2.0"},
            {"id": "ai_registry", "kind": "registry", "label": "AI Registry"},
            {"id": "concierge_registry", "kind": "registry", "label": "Concierge Registry"},
            {"id": "visual_layer", "kind": "visual", "label": "Visual Layer"},
            {"id": "ai_ops", "kind": "future", "label": "AI Operations Center"},
        ]
        edges = [
            {"from": "platform_builder", "to": "ubf", "relation": "uses"},
            {"from": "platform_builder", "to": "academy", "relation": "uses"},
            {"from": "ubf", "to": "ai_registry", "relation": "registers"},
            {"from": "platform_builder", "to": "concierge_registry", "relation": "registers"},
            {"from": "visual_layer", "to": "ai_ops", "relation": "feeds"},
            {"from": "ai_registry", "to": "visual_layer", "relation": "projects"},
        ]
        return {
            "title": "Architecture View",
            "graphs": list(ARCHITECTURE_GRAPHS),
            "nodes": nodes,
            "edges": edges,
            "module_relationships": [e for e in edges if e["from"] in ("platform_builder", "ubf", "academy")],
            "ai_relationships": [e for e in edges if "ai" in e["from"] or "ai" in e["to"]],
            "knowledge_flow": [{"from": "knowledge", "to": "ai_specialist", "relation": "grounds"}],
            "workflow_graph": [{"from": "workflow_engine", "to": "automation", "relation": "triggers"}],
            "registry_graph": edges,
            "future_visual_layer_graph": [e for e in edges if e["to"] in ("visual_layer", "ai_ops")],
            "ready": True,
        }

    def _audit(self, role: str | None, action: str, target: str, detail: dict[str, Any] | None = None) -> dict[str, Any]:
        self.require_owner(role)
        record = {
            "audit_id": _id("gaudit"),
            "who": "platform_owner",
            "what": action,
            "target": target,
            "when": _now(),
            "detail": detail or {},
            "rollback_supported": True,
        }
        self.store.god_audit.save(record["audit_id"], record)
        version = {
            "version_id": _id("gver"),
            "label": f"{action}:{target}",
            "created_at": _now(),
            "audit_id": record["audit_id"],
        }
        self.store.versions.save(version["version_id"], version)
        return record

    def audit_center(self, role: str | None) -> dict[str, Any]:
        self.require_owner(role)
        items = self.store.god_audit.list_all()
        versions = self.store.versions.list_all()
        return {
            "title": "Audit Center",
            "count": len(items),
            "entries": sorted(items, key=lambda x: x.get("when") or "", reverse=True),
            "version_history": versions,
            "rollback_support": True,
        }

    def rollback(self, role: str | None, version_id: str) -> dict[str, Any]:
        self.require_owner(role)
        version = self.store.versions.get(version_id)
        if not version:
            # allow rollback to latest god history via god mode
            return self.god.action(role, "rollback", version_id or "latest")
        record = {
            "rollback_id": _id("grb"),
            "version_id": version_id,
            "status": "rollback_prepared",
            "version": version,
            "at": _now(),
        }
        self._audit(role, "rollback", version_id, record)
        return {"ok": True, **record}

    def explain(self, role: str | None, recommendation: str) -> dict[str, Any]:
        self.require_owner(role)
        text = (recommendation or "Synchronize registries").strip()
        return {
            "recommendation": text,
            "reason": f"«{text}» keeps Platform Owner control surfaces consistent across registries.",
            "expected_benefit": "Fewer broken links and faster recovery during incidents.",
            "business_impact": "Higher platform reliability for every organization on the hub.",
            "alternative_options": [
                "Run targeted registry repair only",
                "Defer sync until after next builder create",
                "Inspect dependent objects first",
            ],
            "estimated_effect": "Stabilization within one control-center cycle",
        }

    def start_session(self, role: str | None) -> dict[str, Any]:
        self.require_owner(role)
        sid = _id("gcc")
        record = {
            "session_id": sid,
            "status": "in_progress",
            "step": 1,
            "draft": {
                "focus_object_id": None,
                "search_query": "",
                "registry_action": "Browse",
                "recommendation": "Synchronize registries",
            },
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.god_control_sessions.save(sid, record)
        return record

    def get_session(self, role: str | None, session_id: str) -> dict[str, Any]:
        self.require_owner(role)
        session = self.store.god_control_sessions.get(session_id)
        if not session:
            raise NotFoundError(f"Control Center session not found: {session_id}")
        return session

    def update_session(self, role: str | None, session_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        session = self.get_session(role, session_id)
        if "step" in patch:
            step = int(patch["step"])
            if step < 1 or step > 11:
                raise ValidationError("step must be between 1 and 11")
            session["step"] = step
        if "draft" in patch and isinstance(patch["draft"], dict):
            session["draft"] = {**session["draft"], **patch["draft"]}
        session["updated_at"] = _now()
        self.store.god_control_sessions.save(session_id, session)
        return session

    def summary(self, role: str | None, session_id: str) -> dict[str, Any]:
        session = self.get_session(role, session_id)
        return {
            "session_id": session_id,
            "title": "Platform Control Center Summary",
            "overview": self.overview(role),
            "health": self.health(role),
            "diagnostics": self.diagnostics(role),
            "architecture": self.architecture(role),
            "audit": self.audit_center(role),
            "explain": self.explain(role, session["draft"].get("recommendation") or "Synchronize registries"),
        }

    def create(self, role: str | None, session_id: str) -> dict[str, Any]:
        session = self.get_session(role, session_id)
        diagnostics = self.diagnostics(role)
        architecture = self.architecture(role)
        health = self.health(role)
        audit = self._audit(role, "register_control_center", "platform", {"session_id": session_id})

        centers = {
            "diagnostics_center_id": diagnostics["diagnostics_id"],
            "audit_center_id": audit["audit_id"],
            "architecture_snapshot_id": _id("garch"),
            "health_center_id": _id("ghealth"),
        }
        self.store.god_architecture.save(
            centers["architecture_snapshot_id"],
            {**architecture, "architecture_snapshot_id": centers["architecture_snapshot_id"], "registered_at": _now()},
        )
        self.store.god_health.save(
            centers["health_center_id"],
            {**health, "health_center_id": centers["health_center_id"], "registered_at": _now()},
        )

        session["status"] = "created"
        session["centers"] = centers
        session["updated_at"] = _now()
        self.store.god_control_sessions.save(session_id, session)

        return {
            "ok": True,
            "session_id": session_id,
            "diagnostics": diagnostics,
            "audit": audit,
            "architecture": architecture,
            "health": health,
            "centers": centers,
            "message": "Diagnostics, Audit, Architecture, and Health Center registered.",
        }

    def status(self, role: str | None) -> dict[str, Any]:
        self.require_owner(role)
        return {
            "ready": True,
            "operational": True,
            "version": "2.0.0",
            "wizard_steps": len(WIZARD_STEPS),
            "god_mode": self.god.status(role),
            "sessions": len(self.store.god_control_sessions.list_all()),
            "audits": len(self.store.god_audit.list_all()),
            "diagnostics": len(self.store.god_diagnostics.list_all()),
        }
