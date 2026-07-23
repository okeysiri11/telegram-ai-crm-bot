"""Tenancy Suite facade — Sprint 20.0."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.tenancy.billing import BillingEngine
from applications.enterprise_hub.tenancy.branding import BrandingEngine
from applications.enterprise_hub.tenancy.isolation import IsolationEngine
from applications.enterprise_hub.tenancy.licensing import LicenseManager
from applications.enterprise_hub.tenancy.onboarding.data_import import DataImportEngine
from applications.enterprise_hub.tenancy.onboarding.migration import MigrationEngine
from applications.enterprise_hub.tenancy.onboarding.setup import OnboardingSetup
from applications.enterprise_hub.tenancy.organization_manager import OrganizationManager
from applications.enterprise_hub.tenancy.organizations.branch import BranchEntity
from applications.enterprise_hub.tenancy.organizations.company import CompanyEntity
from applications.enterprise_hub.tenancy.organizations.department import DepartmentEntity
from applications.enterprise_hub.tenancy.organizations.office import OfficeEntity
from applications.enterprise_hub.tenancy.organizations.warehouse import WarehouseEntity
from applications.enterprise_hub.tenancy.provisioning import ProvisioningEngine
from applications.enterprise_hub.tenancy.routing import TenantRouter
from applications.enterprise_hub.tenancy.tenant_manager import TenantManager
from applications.enterprise_hub.tenancy.tenant_registry import TenantRegistry
from applications.enterprise_hub.tenancy.workspace_manager import WorkspaceManager
from applications.enterprise_hub.tenancy.workspaces.ai import AIWorkspace
from applications.enterprise_hub.tenancy.workspaces.crm import CRMWorkspace
from applications.enterprise_hub.tenancy.workspaces.custom import CustomWorkspace
from applications.enterprise_hub.tenancy.workspaces.erp import ERPWorkspace
from applications.enterprise_hub.tenancy.workspaces.finance import FinanceWorkspace


class TenancySuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = TenantRegistry(self.store)
        self.tenants = TenantManager(self.store)
        self.organizations = OrganizationManager(self.store)
        self.workspaces = WorkspaceManager(self.store)
        self.isolation = IsolationEngine(self.store)
        self.routing = TenantRouter(self.store)
        self.provisioning = ProvisioningEngine(self.store)
        self.branding = BrandingEngine(self.store)
        self.licensing = LicenseManager(self.store)
        self.billing = BillingEngine(self.store)
        self.setup = OnboardingSetup(self.store)
        self.data_import = DataImportEngine(self.store)
        self.migration = MigrationEngine(self.store)
        self.company = CompanyEntity(self.store)
        self.department = DepartmentEntity(self.store)
        self.branch = BranchEntity(self.store)
        self.warehouse = WarehouseEntity(self.store)
        self.office = OfficeEntity(self.store)
        self.crm = CRMWorkspace(self.store)
        self.erp = ERPWorkspace(self.store)
        self.finance_ws = FinanceWorkspace(self.store)
        self.ai_ws = AIWorkspace(self.store)
        self.custom_ws = CustomWorkspace(self.store)

    def bootstrap(self) -> dict[str, Any]:
        setup = self.setup.run(
            name="Bidex Demo Tenant",
            license_tier="enterprise",
            language="en",
            currency="USD",
        )
        tenant_id = setup["tenant_id"]

        holding = self.organizations.create_node(
            tenant_id=tenant_id, name="Bidex Holding", level="holding"
        )
        company = self.company.create(
            tenant_id=tenant_id, name="Bidex CRM Co", parent_id=holding["org_id"]
        )
        branch = self.branch.create(
            tenant_id=tenant_id, name="EU Branch", parent_id=company["org_id"]
        )
        dept = self.department.create(
            tenant_id=tenant_id, name="Sales", parent_id=branch["org_id"]
        )
        team = self.organizations.create_node(
            tenant_id=tenant_id, name="Enterprise Sales", level="team", parent_id=dept["org_id"]
        )
        employee = self.organizations.create_node(
            tenant_id=tenant_id, name="Alex Admin", level="employee", parent_id=team["org_id"]
        )
        warehouse = self.warehouse.create(
            tenant_id=tenant_id, name="Central Warehouse", parent_id=company["org_id"]
        )
        office = self.office.create(
            tenant_id=tenant_id, name="HQ Office", parent_id=company["org_id"]
        )

        env = self.tenants.attach_environment(
            tenant_id=tenant_id, name="prod-primary", env_type="production"
        )

        for scope in ("data", "files", "ai_context", "api", "queues", "logs", "backups"):
            self.isolation.enforce(tenant_id=tenant_id, scope=scope, resource_key=f"default-{scope}")

        route = self.routing.route(
            tenant_id=tenant_id, target="crm", path="/deals", workspace_id=None
        )

        sub = self.billing.subscribe(tenant_id=tenant_id, plan="enterprise", amount=999.0)
        inv = self.billing.invoice(
            tenant_id=tenant_id, subscription_id=sub["subscription_id"], amount=999.0
        )
        pay = self.billing.pay(invoice_id=inv["invoice_id"], method="card")
        limits = self.billing.set_limits(
            tenant_id=tenant_id, limits={"users": 5000, "workspaces": 100}
        )

        usage = self.tenants.record_usage(
            tenant_id=tenant_id, active_users=42, ai_cost=18.5, module="crm"
        )
        analytics = self.tenants.analytics(tenant_id=tenant_id)

        custom = self.custom_ws.create(tenant_id=tenant_id, name="Partner Portal")
        exported = self.migration.export_workspace(workspace_id=custom["workspace_id"])
        imported = self.migration.import_workspace(
            tenant_id=tenant_id, payload={"name": "Partner Portal Copy", "kind": "custom"}
        )
        data_imp = self.data_import.import_records(
            tenant_id=tenant_id,
            source="csv",
            records=[{"name": "Acme", "type": "account"}],
        )

        hierarchy = self.organizations.hierarchy(tenant_id=tenant_id)

        return {
            "bootstrap": True,
            "setup_id": setup["setup_id"],
            "tenant_id": tenant_id,
            "holding_id": holding["org_id"],
            "company_id": company["org_id"],
            "branch_id": branch["org_id"],
            "department_id": dept["org_id"],
            "team_id": team["org_id"],
            "employee_id": employee["org_id"],
            "warehouse_id": warehouse["org_id"],
            "office_id": office["org_id"],
            "environment_id": env["environment_id"],
            "route_id": route["route_id"],
            "subscription_id": sub["subscription_id"],
            "invoice_id": inv["invoice_id"],
            "payment_id": pay["payment_id"],
            "limit_id": limits["limit_id"],
            "usage_id": usage["usage_id"],
            "analytics_id": analytics["analytics_id"],
            "export_id": exported["export_id"],
            "imported_workspace_id": imported["workspace_id"],
            "import_id": data_imp["import_id"],
            "hierarchy_count": hierarchy["count"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "registry": self.registry.status(),
            "tenants": self.tenants.status(),
            "organizations": self.organizations.status(),
            "workspaces": self.workspaces.status(),
            "isolation": self.isolation.status(),
            "routing": self.routing.status(),
            "provisioning": self.provisioning.status(),
            "branding": self.branding.status(),
            "licensing": self.licensing.status(),
            "billing": self.billing.status(),
        }


tenancy = TenancySuite()
