# BI security — role-based dashboard and report access.

from __future__ import annotations

from applications.auto_marketplace.business_intelligence.models import DashboardRole


_PERMISSIONS: dict[DashboardRole, set[str]] = {
    DashboardRole.OWNER: {"*"},
    DashboardRole.ADMINISTRATOR: {
        "bi.read", "bi.write", "dashboard.all", "reports.all", "forecast.all", "kpi.all", "analytics.all",
    },
    DashboardRole.FINANCE_MANAGER: {
        "bi.read", "dashboard.finance", "reports.financial", "forecast.revenue", "forecast.cashflow",
        "kpi.financial", "analytics.financial",
    },
    DashboardRole.SALES_MANAGER: {
        "bi.read", "dashboard.sales", "reports.sales", "forecast.sales", "kpi.sales", "analytics.sales",
    },
    DashboardRole.DEALER: {"bi.read", "dashboard.dealer", "kpi.dealer", "analytics.dealer"},
    DashboardRole.OPERATIONS: {"bi.read", "dashboard.operations", "analytics.inventory", "analytics.workflow"},
    DashboardRole.AI_AGENT: {"bi.read", "dashboard.ai", "insights.generate", "forecast.all", "analytics.all"},
}


class BISecurity:
    def authorize(self, role: DashboardRole | str, permission: str) -> bool:
        if isinstance(role, str):
            try:
                role = DashboardRole(role)
            except ValueError:
                return False
        perms = _PERMISSIONS.get(role, set())
        if "*" in perms:
            return True
        return permission in perms

    def require(self, role: DashboardRole | str, permission: str) -> None:
        from applications.auto_marketplace.shared.exceptions import AuthorizationError

        if not self.authorize(role, permission):
            raise AuthorizationError(f"Permission denied: {permission}")


bi_security = BISecurity()
