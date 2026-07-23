"""Provisioning engine — workspace, roles, AI agents, templates, integrations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.tenancy.tenant_registry import TenantRegistry
from applications.enterprise_hub.tenancy.workspace_manager import WorkspaceManager


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


DEFAULT_ROLES = ("owner", "admin", "manager", "member", "viewer")
DEFAULT_AGENTS = ("crm_agent", "ops_agent", "support_agent")
DEFAULT_TEMPLATES = ("onboarding", "sales_pipeline", "support_desk")
DEFAULT_INTEGRATIONS = ("email", "calendar", "storage")


class ProvisioningEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tenants = TenantRegistry(self.store)
        self.workspaces = WorkspaceManager(self.store)

    def provision(self, *, tenant_id: str, include_ai: bool = True) -> dict[str, Any]:
        self.tenants.get(tenant_id)
        ws_ids = []
        for kind, label in (
            ("crm", "CRM Workspace"),
            ("erp", "ERP Workspace"),
            ("finance", "Finance Workspace"),
            ("ai", "AI Workspace"),
            ("documents", "Documents Workspace"),
        ):
            ws = self.workspaces.create(tenant_id=tenant_id, name=label, kind=kind)
            ws_ids.append(ws["workspace_id"])

        roles = []
        for role in DEFAULT_ROLES:
            rid = _id("tn_role")
            roles.append(
                self.store.tn_roles.save(
                    rid,
                    {
                        "role_id": rid,
                        "tenant_id": tenant_id,
                        "name": role,
                        "permissions": ["*"] if role in ("owner", "admin") else ["read"],
                        "created_at": _now(),
                    },
                )
            )

        agents = []
        if include_ai:
            for agent in DEFAULT_AGENTS:
                aid = _id("tn_agt")
                agents.append(
                    self.store.tn_agents.save(
                        aid,
                        {
                            "agent_id": aid,
                            "tenant_id": tenant_id,
                            "name": agent,
                            "status": "ready",
                            "created_at": _now(),
                        },
                    )
                )

        templates = []
        for tpl in DEFAULT_TEMPLATES:
            tid = _id("tn_tpl")
            templates.append(
                self.store.tn_templates.save(
                    tid,
                    {
                        "template_id": tid,
                        "tenant_id": tenant_id,
                        "name": tpl,
                        "created_at": _now(),
                    },
                )
            )

        integrations = []
        for integ in DEFAULT_INTEGRATIONS:
            iid = _id("tn_int")
            integrations.append(
                self.store.tn_integrations.save(
                    iid,
                    {
                        "integration_id": iid,
                        "tenant_id": tenant_id,
                        "name": integ,
                        "status": "configured",
                        "created_at": _now(),
                    },
                )
            )

        pid = _id("tn_prov")
        return self.store.tn_provisions.save(
            pid,
            {
                "provision_id": pid,
                "tenant_id": tenant_id,
                "workspace_ids": ws_ids,
                "role_ids": [r["role_id"] for r in roles],
                "agent_ids": [a["agent_id"] for a in agents],
                "template_ids": [t["template_id"] for t in templates],
                "integration_ids": [i["integration_id"] for i in integrations],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "provisions": self.store.tn_provisions.count(),
            "roles": self.store.tn_roles.count(),
            "agents": self.store.tn_agents.count(),
            "templates": self.store.tn_templates.count(),
            "integrations": self.store.tn_integrations.count(),
        }
