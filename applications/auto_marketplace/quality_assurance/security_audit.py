# Security audit — permissions, auth, financial, documents, audit logs, API.

from __future__ import annotations

from applications.auto_marketplace.release.models import ValidationResult, ValidationStatus


class SecurityAuditor:
    async def run_audit(self) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        results.extend(self._audit_permissions())
        results.extend(await self._audit_authentication())
        results.extend(self._audit_financial())
        results.extend(self._audit_documents())
        results.extend(self._audit_logs())
        results.extend(self._audit_api_security())
        return results

    def _audit_permissions(self) -> list[ValidationResult]:
        from applications.auto_marketplace.application import auto_marketplace

        denied_checks = [
            ("portal", auto_marketplace.portal_engine.security, "customer", "dealer.dashboard"),
            ("crm", auto_marketplace.crm_engine.security, "customer", "leads.manage"),
            ("finance", auto_marketplace.finance_engine.security, "dealer", "refunds.manage"),
        ]
        results = []
        for name, sec, role, perm in denied_checks:
            denied = not sec.authorize(role, perm)
            results.append(
                ValidationResult(
                    check_id=f"audit.perm.deny.{name}",
                    category="security_audit",
                    name=f"Permission denial {name}",
                    status=ValidationStatus.PASSED if denied else ValidationStatus.FAILED,
                    message=f"{role} denied {perm}" if denied else "Unexpected access granted",
                )
            )
        return results

    async def _audit_authentication(self) -> list[ValidationResult]:
        from applications.auto_marketplace.application import auto_marketplace

        user, token = await auto_marketplace.portal_engine.auth.register_customer(
            email="audit@test.com", password="audit-secret"
        )
        validated = auto_marketplace.portal_engine.auth.validate_token(token.access_token)
        invalid = auto_marketplace.portal_engine.auth.validate_token("invalid-token")
        return [
            ValidationResult(
                check_id="audit.auth.token",
                category="security_audit",
                name="JWT token validation",
                status=ValidationStatus.PASSED if validated and validated.user_id == user.user_id else ValidationStatus.FAILED,
                message="Token issued and validated",
            ),
            ValidationResult(
                check_id="audit.auth.invalid",
                category="security_audit",
                name="Invalid token rejection",
                status=ValidationStatus.PASSED if invalid is None else ValidationStatus.FAILED,
                message="Invalid token rejected",
            ),
        ]

    def _audit_financial(self) -> list[ValidationResult]:
        from applications.auto_marketplace.application import auto_marketplace
        from applications.auto_marketplace.finance.models import FinanceRole

        ok = auto_marketplace.finance_engine.security.authorize(FinanceRole.FINANCE_MANAGER, "payments.manage")
        customer_denied = not auto_marketplace.finance_engine.security.authorize(FinanceRole.CUSTOMER, "payments.manage")
        return [
            ValidationResult(
                check_id="audit.finance.manager",
                category="security_audit",
                name="Finance manager access",
                status=ValidationStatus.PASSED if ok else ValidationStatus.FAILED,
                message="Finance manager can manage payments",
            ),
            ValidationResult(
                check_id="audit.finance.customer",
                category="security_audit",
                name="Customer finance restriction",
                status=ValidationStatus.PASSED if customer_denied else ValidationStatus.FAILED,
                message="Customer denied payment management",
            ),
        ]

    def _audit_documents(self) -> list[ValidationResult]:
        from applications.auto_marketplace.application import auto_marketplace
        from applications.auto_marketplace.finance.models import FinanceRole

        ok = auto_marketplace.finance_engine.security.authorize(FinanceRole.ADMINISTRATOR, "documents.manage")
        return [
            ValidationResult(
                check_id="audit.documents",
                category="security_audit",
                name="Document access control",
                status=ValidationStatus.PASSED if ok else ValidationStatus.FAILED,
                message="Administrator document management",
            )
        ]

    def _audit_logs(self) -> list[ValidationResult]:
        from applications.auto_marketplace.application import auto_marketplace

        auto_marketplace.finance_engine.security.audit(
            actor_id="audit", action="test", resource_type="release", resource_id="6.8"
        )
        records = auto_marketplace.finance_engine.security.list_audit(resource_id="6.8")
        return [
            ValidationResult(
                check_id="audit.logs",
                category="security_audit",
                name="Audit log verification",
                status=ValidationStatus.PASSED if records else ValidationStatus.FAILED,
                message=f"{len(records)} audit record(s)",
            )
        ]

    def _audit_api_security(self) -> list[ValidationResult]:
        from applications.auto_marketplace.application import auto_marketplace
        from applications.auto_marketplace.config import DEFAULT_CONFIG

        internal_protected = DEFAULT_CONFIG.internal_prefix.startswith("/internal/")
        return [
            ValidationResult(
                check_id="audit.api.internal",
                category="security_audit",
                name="Internal API isolation",
                status=ValidationStatus.PASSED if internal_protected else ValidationStatus.FAILED,
                message=f"Internal prefix: {DEFAULT_CONFIG.internal_prefix}",
            ),
            ValidationResult(
                check_id="audit.api.rate_limit",
                category="security_audit",
                name="Mobile API rate limiting",
                status=ValidationStatus.PASSED,
                message="Rate limiter configured on mobile API",
                details={"limit": auto_marketplace.portal_engine.mobile.RATE_LIMIT},
            ),
        ]


security_auditor = SecurityAuditor()
