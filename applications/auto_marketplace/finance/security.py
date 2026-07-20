# Finance RBAC — role-based permissions and audit logging.

from __future__ import annotations

from applications.auto_marketplace.finance.models import AuditRecord, FinanceRole
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


_PERMISSIONS: dict[FinanceRole, set[str]] = {
    FinanceRole.OWNER: {"*"},
    FinanceRole.ADMINISTRATOR: {
        "finance.read", "finance.write", "finance.delete",
        "documents.read", "documents.manage", "contracts.read", "contracts.manage",
        "payments.read", "payments.manage", "invoices.read", "invoices.manage",
        "refunds.manage", "settlements.manage", "reports.view",
    },
    FinanceRole.FINANCE_MANAGER: {
        "finance.read", "finance.write",
        "documents.read", "documents.manage", "contracts.read", "contracts.manage",
        "payments.read", "payments.manage", "invoices.read", "invoices.manage",
        "refunds.manage", "settlements.manage", "reports.view",
    },
    FinanceRole.SALES_MANAGER: {
        "finance.read", "documents.read", "documents.write", "contracts.read", "contracts.write",
        "invoices.read", "payments.read",
    },
    FinanceRole.DEALER: {"finance.read", "documents.read", "contracts.read", "payments.read", "invoices.read"},
    FinanceRole.CUSTOMER: {"finance.read.self", "documents.read.self", "invoices.read.self", "payments.read.self"},
    FinanceRole.AI_AGENT: {
        "finance.read", "documents.read", "documents.generate", "contracts.analyze",
        "payments.detect", "invoices.read", "reports.view",
    },
}


class FinanceSecurity:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def authorize(self, role: FinanceRole | str, permission: str) -> bool:
        if isinstance(role, str):
            try:
                role = FinanceRole(role)
            except ValueError:
                return False
        perms = _PERMISSIONS.get(role, set())
        if "*" in perms:
            return True
        return permission in perms

    def require(self, role: FinanceRole | str, permission: str) -> None:
        from applications.auto_marketplace.shared.exceptions import AuthorizationError

        if not self.authorize(role, permission):
            raise AuthorizationError(f"Permission denied: {permission}")

    def audit(
        self,
        *,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict | None = None,
    ) -> AuditRecord:
        record = AuditRecord(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
        )
        self._store.audit_records.save(record.audit_id, record)
        return record

    def list_audit(self, resource_id: str | None = None) -> list[AuditRecord]:
        records = self._store.audit_records.list_all()
        if resource_id:
            return [r for r in records if r.resource_id == resource_id]
        return records


finance_security = FinanceSecurity()
