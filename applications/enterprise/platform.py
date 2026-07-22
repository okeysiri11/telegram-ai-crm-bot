"""Enterprise Platform — org/tenant/workspace hierarchy (Sprint 12.5)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise.shared.store import EnterpriseStore, enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EnterprisePlatform:
    def __init__(self, store: EnterpriseStore | None = None) -> None:
        self.store = store or enterprise_store

    def create_organization(self, *, name: str, domain: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("organization name required")
        org_id = _id("org")
        org = {
            "organization_id": org_id,
            "name": name,
            "domain": domain,
            "status": "active",
            "created_at": _now(),
        }
        return self.store.organizations.save(org_id, org)

    def create_tenant(self, *, organization_id: str, name: str) -> dict[str, Any]:
        if self.store.organizations.get(organization_id) is None:
            raise NotFoundError("organization", organization_id)
        tid = _id("tenant")
        tenant = {
            "tenant_id": tid,
            "organization_id": organization_id,
            "name": name,
            "status": "active",
            "created_at": _now(),
        }
        return self.store.tenants.save(tid, tenant)

    def create_workspace(self, *, tenant_id: str, name: str) -> dict[str, Any]:
        if self.store.tenants.get(tenant_id) is None:
            raise NotFoundError("tenant", tenant_id)
        wid = _id("ws")
        ws = {
            "workspace_id": wid,
            "tenant_id": tenant_id,
            "name": name,
            "status": "active",
            "created_at": _now(),
        }
        return self.store.workspaces.save(wid, ws)

    def create_company(self, *, organization_id: str, name: str) -> dict[str, Any]:
        if self.store.organizations.get(organization_id) is None:
            raise NotFoundError("organization", organization_id)
        cid = _id("co")
        company = {
            "company_id": cid,
            "organization_id": organization_id,
            "name": name,
            "status": "active",
            "created_at": _now(),
        }
        return self.store.companies.save(cid, company)

    def create_department(self, *, company_id: str, name: str) -> dict[str, Any]:
        if self.store.companies.get(company_id) is None:
            raise NotFoundError("company", company_id)
        did = _id("dept")
        dept = {
            "department_id": did,
            "company_id": company_id,
            "name": name,
            "status": "active",
            "created_at": _now(),
        }
        return self.store.departments.save(did, dept)

    def create_project(self, *, department_id: str, name: str) -> dict[str, Any]:
        if self.store.departments.get(department_id) is None:
            raise NotFoundError("department", department_id)
        pid = _id("proj")
        project = {
            "project_id": pid,
            "department_id": department_id,
            "name": name,
            "status": "active",
            "created_at": _now(),
        }
        return self.store.projects.save(pid, project)

    def set_global_setting(self, *, key: str, value: Any) -> dict[str, Any]:
        if not key:
            raise ValidationError("setting key required")
        entry = {"key": key, "value": value, "updated_at": _now()}
        return self.store.settings.save(key, entry)

    def get_global_setting(self, key: str) -> dict[str, Any]:
        item = self.store.settings.get(key)
        if item is None:
            raise NotFoundError("setting", key)
        return item

    def status(self) -> dict[str, Any]:
        return {
            "organizations": len(self.store.organizations.list_all()),
            "tenants": len(self.store.tenants.list_all()),
            "workspaces": len(self.store.workspaces.list_all()),
            "companies": len(self.store.companies.list_all()),
            "departments": len(self.store.departments.list_all()),
            "projects": len(self.store.projects.list_all()),
            "settings": len(self.store.settings.list_all()),
        }


enterprise_platform = EnterprisePlatform()
