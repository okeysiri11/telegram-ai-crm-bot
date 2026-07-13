# Tenant Billing Engine v1 — subscriptions, usage, invoices.

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.partner_tenant_engine import TenantResourceType, TenantRoleCode
from database.models.tenant_billing_engine import (
    BillingPlanCode,
    InvoiceStatus,
    SubscriptionStatus,
    UsageBillingType,
)
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.partner_tenant_repository import (
    PartnerTenantRepository,
    TenantResourceBindingRepository,
    TenantUserRoleRepository,
)
from repositories.tenant_billing_repository import (
    TenantInvoiceLineRepository,
    TenantInvoiceRepository,
    TenantSubscriptionRepository,
    TenantUsageRepository,
)
from repositories.user_role_repository import UserRoleRepository
from services.pg_partner_tenant_engine import (
    PartnerTenantEngineV1,
    TenantAccessDeniedError,
)

MONEY = Decimal("0.01")
PLATFORM_ADMIN_ROLES = frozenset({"OWNER", "ADMIN"})
TAX_RATE = Decimal("0.00")


@dataclass(frozen=True)
class PlanConfig:
    monthly_fee: Decimal
    included_leads: int
    included_managers: int
    included_channels: int
    per_lead_rate: Decimal
    per_manager_rate: Decimal
    per_channel_rate: Decimal
    usage_unit_price: Decimal


PLAN_CATALOG: dict[str, PlanConfig] = {
    BillingPlanCode.STARTER.value: PlanConfig(
        monthly_fee=Decimal("99.00"),
        included_leads=50,
        included_managers=2,
        included_channels=1,
        per_lead_rate=Decimal("2.50"),
        per_manager_rate=Decimal("35.00"),
        per_channel_rate=Decimal("25.00"),
        usage_unit_price=Decimal("0.10"),
    ),
    BillingPlanCode.PRO.value: PlanConfig(
        monthly_fee=Decimal("299.00"),
        included_leads=250,
        included_managers=5,
        included_channels=3,
        per_lead_rate=Decimal("1.75"),
        per_manager_rate=Decimal("29.00"),
        per_channel_rate=Decimal("19.00"),
        usage_unit_price=Decimal("0.06"),
    ),
    BillingPlanCode.BUSINESS.value: PlanConfig(
        monthly_fee=Decimal("799.00"),
        included_leads=1000,
        included_managers=15,
        included_channels=8,
        per_lead_rate=Decimal("1.25"),
        per_manager_rate=Decimal("22.00"),
        per_channel_rate=Decimal("14.00"),
        usage_unit_price=Decimal("0.04"),
    ),
    BillingPlanCode.ENTERPRISE.value: PlanConfig(
        monthly_fee=Decimal("1999.00"),
        included_leads=5000,
        included_managers=50,
        included_channels=25,
        per_lead_rate=Decimal("0.90"),
        per_manager_rate=Decimal("18.00"),
        per_channel_rate=Decimal("10.00"),
        usage_unit_price=Decimal("0.02"),
    ),
}


class TenantBillingEngineError(Exception):
    pass


class TenantBillingEngineV1:
    @staticmethod
    def _quantize(amount: Decimal) -> Decimal:
        return amount.quantize(MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    async def is_platform_admin(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in PLATFORM_ADMIN_ROLES for role in roles)

    @staticmethod
    def _plan_snapshot(plan_code: str) -> dict[str, Any]:
        plan = PLAN_CATALOG[plan_code]
        return {
            "plan_code": plan_code,
            "monthly_fee": str(plan.monthly_fee),
            "included_leads": plan.included_leads,
            "included_managers": plan.included_managers,
            "included_channels": plan.included_channels,
            "per_lead_rate": str(plan.per_lead_rate),
            "per_manager_rate": str(plan.per_manager_rate),
            "per_channel_rate": str(plan.per_channel_rate),
            "usage_unit_price": str(plan.usage_unit_price),
        }

    @staticmethod
    def _subscription_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "company_id": str(row.company_id),
            "plan_code": row.plan_code,
            "status": row.status,
            "currency": row.currency,
            "current_period_start": row.current_period_start.isoformat(),
            "current_period_end": row.current_period_end.isoformat(),
            "plan": TenantBillingEngineV1._plan_snapshot(row.plan_code),
        }

    @staticmethod
    def _usage_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "billing_type": row.billing_type,
            "quantity": str(row.quantity),
            "unit_price": str(row.unit_price),
            "amount": str(row.amount),
            "reference_key": row.reference_key,
            "recorded_at": row.recorded_at.isoformat(),
            "invoice_id": str(row.invoice_id) if row.invoice_id else None,
        }

    @staticmethod
    def _line_snapshot(line) -> dict[str, Any]:
        return {
            "id": str(line.id),
            "line_type": line.line_type,
            "description": line.description,
            "quantity": str(line.quantity),
            "unit_price": str(line.unit_price),
            "amount": str(line.amount),
        }

    @staticmethod
    def _invoice_snapshot(invoice, lines: list | None = None) -> dict[str, Any]:
        payload = {
            "id": str(invoice.id),
            "tenant_id": str(invoice.tenant_id),
            "company_id": str(invoice.company_id),
            "invoice_number": invoice.invoice_number,
            "period_start": invoice.period_start.isoformat(),
            "period_end": invoice.period_end.isoformat(),
            "status": invoice.status,
            "currency": invoice.currency,
            "subtotal": str(invoice.subtotal),
            "tax": str(invoice.tax),
            "total": str(invoice.total),
            "issued_at": invoice.issued_at.isoformat(),
            "due_at": invoice.due_at.isoformat() if invoice.due_at else None,
            "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None,
            "metadata": invoice.metadata_ or {},
        }
        if lines is not None:
            payload["lines"] = [TenantBillingEngineV1._line_snapshot(line) for line in lines]
        return payload

    @staticmethod
    def _month_period(reference: date | None = None) -> tuple[date, date]:
        today = reference or datetime.now(timezone.utc).date()
        start = today.replace(day=1)
        if start.month == 12:
            end = date(start.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(start.year, start.month + 1, 1) - timedelta(days=1)
        return start, end

    @staticmethod
    async def _audit(
        session,
        *,
        actor_id: int,
        action: str,
        entity_id: str,
        company_id: uuid.UUID,
        tenant_id: uuid.UUID,
        new_value: dict | None = None,
    ) -> None:
        await AuditRepository(session).create_log(
            user_id=actor_id,
            company_id=company_id,
            tenant_id=tenant_id,
            entity_type="tenant_billing",
            entity_id=entity_id,
            action=action,
            new_value=new_value,
        )

    @staticmethod
    async def list_plans() -> list[dict[str, Any]]:
        return [TenantBillingEngineV1._plan_snapshot(code) for code in PLAN_CATALOG]

    @staticmethod
    async def subscribe_tenant(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        plan_code: str,
        currency: str = "USD",
    ) -> dict[str, Any]:
        if not await TenantBillingEngineV1.is_platform_admin(actor_id):
            raise TenantAccessDeniedError("Platform admin access required")
        if plan_code not in PLAN_CATALOG:
            raise TenantBillingEngineError(f"Invalid plan: {plan_code}")

        async with get_session() as session:
            tenant = await PartnerTenantRepository(session).get_by_id(tenant_id)
            if tenant is None:
                raise TenantBillingEngineError(f"Tenant not found: {tenant_id}")

            period_start, period_end = TenantBillingEngineV1._month_period()
            subscription = await TenantSubscriptionRepository(session).upsert(
                tenant_id=tenant_id,
                company_id=tenant.company_id,
                plan_code=plan_code,
                currency=currency,
                current_period_start=period_start,
                current_period_end=period_end,
            )
            await TenantBillingEngineV1._audit(
                session,
                actor_id=actor_id,
                action=AuditAction.CREATE.value,
                entity_id=str(subscription.id),
                company_id=tenant.company_id,
                tenant_id=tenant_id,
                new_value=TenantBillingEngineV1._subscription_snapshot(subscription),
            )
            return TenantBillingEngineV1._subscription_snapshot(subscription)

    @staticmethod
    async def get_subscription(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any] | None:
        await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
        async with get_session() as session:
            row = await TenantSubscriptionRepository(session).get_by_tenant(tenant_id)
            return TenantBillingEngineV1._subscription_snapshot(row) if row else None

    @staticmethod
    async def record_usage(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        quantity: Decimal,
        reference_key: str | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        ctx = await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
        subscription = await TenantBillingEngineV1._require_subscription(tenant_id)
        plan = PLAN_CATALOG[subscription["plan_code"]]
        unit_price = plan.usage_unit_price
        amount = TenantBillingEngineV1._quantize(quantity * unit_price)
        now = datetime.now(timezone.utc)

        async with get_session() as session:
            row = await TenantUsageRepository(session).record(
                tenant_id=ctx.tenant_id,
                company_id=ctx.company_id,
                billing_type=UsageBillingType.USAGE.value,
                quantity=quantity,
                unit_price=unit_price,
                amount=amount,
                recorded_at=now,
                reference_key=reference_key,
                metadata=metadata,
            )
            return TenantBillingEngineV1._usage_snapshot(row)

    @staticmethod
    async def record_lead(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        lead_id: str,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        ctx = await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
        subscription = await TenantBillingEngineV1._require_subscription(tenant_id)
        plan = PLAN_CATALOG[subscription["plan_code"]]
        now = datetime.now(timezone.utc)

        async with get_session() as session:
            row = await TenantUsageRepository(session).record(
                tenant_id=ctx.tenant_id,
                company_id=ctx.company_id,
                billing_type=UsageBillingType.PER_LEAD.value,
                quantity=Decimal("1"),
                unit_price=plan.per_lead_rate,
                amount=plan.per_lead_rate,
                recorded_at=now,
                reference_key=f"lead:{lead_id}",
                metadata=metadata,
            )
            return TenantBillingEngineV1._usage_snapshot(row)

    @staticmethod
    async def record_manager(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        manager_id: int,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        ctx = await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
        subscription = await TenantBillingEngineV1._require_subscription(tenant_id)
        plan = PLAN_CATALOG[subscription["plan_code"]]
        now = datetime.now(timezone.utc)

        async with get_session() as session:
            row = await TenantUsageRepository(session).record(
                tenant_id=ctx.tenant_id,
                company_id=ctx.company_id,
                billing_type=UsageBillingType.PER_MANAGER.value,
                quantity=Decimal("1"),
                unit_price=plan.per_manager_rate,
                amount=plan.per_manager_rate,
                recorded_at=now,
                reference_key=f"manager:{manager_id}",
                metadata=metadata,
            )
            return TenantBillingEngineV1._usage_snapshot(row)

    @staticmethod
    async def record_channel(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        channel_key: str,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        ctx = await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
        subscription = await TenantBillingEngineV1._require_subscription(tenant_id)
        plan = PLAN_CATALOG[subscription["plan_code"]]
        now = datetime.now(timezone.utc)

        async with get_session() as session:
            row = await TenantUsageRepository(session).record(
                tenant_id=ctx.tenant_id,
                company_id=ctx.company_id,
                billing_type=UsageBillingType.PER_CHANNEL.value,
                quantity=Decimal("1"),
                unit_price=plan.per_channel_rate,
                amount=plan.per_channel_rate,
                recorded_at=now,
                reference_key=f"channel:{channel_key}",
                metadata=metadata,
            )
            return TenantBillingEngineV1._usage_snapshot(row)

    @staticmethod
    async def _require_subscription(tenant_id: uuid.UUID) -> dict[str, Any]:
        async with get_session() as session:
            row = await TenantSubscriptionRepository(session).get_by_tenant(tenant_id)
            if row is None:
                raise TenantBillingEngineError("Tenant subscription not found")
            if row.status != SubscriptionStatus.ACTIVE.value:
                raise TenantBillingEngineError("Tenant subscription is not active")
            return TenantBillingEngineV1._subscription_snapshot(row)

    @staticmethod
    async def collect_tenant_usage(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await TenantBillingEngineV1.is_platform_admin(actor_id):
            await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

        subscription = await TenantBillingEngineV1._require_subscription(tenant_id)
        plan = PLAN_CATALOG[subscription["plan_code"]]
        period_start = date.fromisoformat(subscription["current_period_start"])
        period_end = date.fromisoformat(subscription["current_period_end"])
        now = datetime.now(timezone.utc)

        async with get_session() as session:
            tenant = await PartnerTenantRepository(session).get_by_id(tenant_id)
            if tenant is None:
                raise TenantBillingEngineError(f"Tenant not found: {tenant_id}")

            leads = await TenantResourceBindingRepository(session).list_by_tenant(
                tenant_id,
                resource_type=TenantResourceType.LEAD.value,
            )
            managers = await TenantUserRoleRepository(session).list_by_tenant(tenant_id)
            manager_count = sum(
                1
                for row in managers
                if row.role_code
                in {TenantRoleCode.TENANT_MANAGER.value, TenantRoleCode.TENANT_ADMIN.value}
            )
            channels = await TenantResourceBindingRepository(session).list_by_tenant(
                tenant_id,
                resource_type=TenantResourceType.CAMPAIGN.value,
            )

            usage_repo = TenantUsageRepository(session)
            recorded: list[dict[str, Any]] = []

            for lead in leads:
                row = await usage_repo.record(
                    tenant_id=tenant_id,
                    company_id=tenant.company_id,
                    billing_type=UsageBillingType.PER_LEAD.value,
                    quantity=Decimal("1"),
                    unit_price=plan.per_lead_rate,
                    amount=plan.per_lead_rate,
                    recorded_at=now,
                    reference_key=f"lead:{lead.resource_id}",
                )
                recorded.append(TenantBillingEngineV1._usage_snapshot(row))

            for manager in managers:
                if manager.role_code not in {
                    TenantRoleCode.TENANT_MANAGER.value,
                    TenantRoleCode.TENANT_ADMIN.value,
                }:
                    continue
                row = await usage_repo.record(
                    tenant_id=tenant_id,
                    company_id=tenant.company_id,
                    billing_type=UsageBillingType.PER_MANAGER.value,
                    quantity=Decimal("1"),
                    unit_price=plan.per_manager_rate,
                    amount=plan.per_manager_rate,
                    recorded_at=now,
                    reference_key=f"manager:{manager.user_id}",
                )
                recorded.append(TenantBillingEngineV1._usage_snapshot(row))

            for channel in channels:
                row = await usage_repo.record(
                    tenant_id=tenant_id,
                    company_id=tenant.company_id,
                    billing_type=UsageBillingType.PER_CHANNEL.value,
                    quantity=Decimal("1"),
                    unit_price=plan.per_channel_rate,
                    amount=plan.per_channel_rate,
                    recorded_at=now,
                    reference_key=f"channel:{channel.resource_id}",
                )
                recorded.append(TenantBillingEngineV1._usage_snapshot(row))

            aggregates = await usage_repo.aggregate_uninvoiced(
                tenant_id,
                period_start=period_start,
                period_end=period_end,
            )

        return {
            "tenant_id": str(tenant_id),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "counts": {
                "leads": len(leads),
                "managers": manager_count,
                "channels": len(channels),
            },
            "recorded": recorded,
            "aggregates": {
                key: {"quantity": str(v["quantity"]), "amount": str(v["amount"])}
                for key, v in aggregates.items()
            },
        }

    @staticmethod
    async def _build_invoice_lines(
        session,
        *,
        tenant_id: uuid.UUID,
        plan_code: str,
        period_start: date,
        period_end: date,
    ) -> list[dict[str, Any]]:
        plan = PLAN_CATALOG[plan_code]
        usage_repo = TenantUsageRepository(session)
        aggregates = await usage_repo.aggregate_uninvoiced(
            tenant_id,
            period_start=period_start,
            period_end=period_end,
        )

        lines: list[dict[str, Any]] = []
        lines.append({
            "line_type": UsageBillingType.MONTHLY_SUBSCRIPTION.value,
            "description": f"{plan_code} monthly subscription",
            "quantity": Decimal("1"),
            "unit_price": plan.monthly_fee,
            "amount": plan.monthly_fee,
        })

        def _overage_line(
            billing_type: str,
            label: str,
            included: int,
            unit_price: Decimal,
        ) -> None:
            data = aggregates.get(billing_type, {"quantity": Decimal("0"), "amount": Decimal("0")})
            qty = int(data["quantity"])
            overage_qty = max(0, qty - included)
            if overage_qty <= 0:
                return
            amount = TenantBillingEngineV1._quantize(Decimal(overage_qty) * unit_price)
            lines.append({
                "line_type": billing_type,
                "description": f"{label} overage ({overage_qty} × {unit_price})",
                "quantity": Decimal(overage_qty),
                "unit_price": unit_price,
                "amount": amount,
            })

        _overage_line(
            UsageBillingType.PER_LEAD.value,
            "Lead billing",
            plan.included_leads,
            plan.per_lead_rate,
        )
        _overage_line(
            UsageBillingType.PER_MANAGER.value,
            "Manager billing",
            plan.included_managers,
            plan.per_manager_rate,
        )
        _overage_line(
            UsageBillingType.PER_CHANNEL.value,
            "Channel billing",
            plan.included_channels,
            plan.per_channel_rate,
        )

        usage_data = aggregates.get(
            UsageBillingType.USAGE.value,
            {"quantity": Decimal("0"), "amount": Decimal("0")},
        )
        if usage_data["amount"] > 0:
            qty = usage_data["quantity"]
            unit = plan.usage_unit_price if qty == 0 else TenantBillingEngineV1._quantize(
                usage_data["amount"] / qty
            )
            lines.append({
                "line_type": UsageBillingType.USAGE.value,
                "description": "Usage-based billing",
                "quantity": qty,
                "unit_price": unit,
                "amount": TenantBillingEngineV1._quantize(usage_data["amount"]),
            })

        return lines

    @staticmethod
    async def generate_invoice(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> dict[str, Any]:
        if not await TenantBillingEngineV1.is_platform_admin(actor_id):
            await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

        async with get_session() as session:
            tenant = await PartnerTenantRepository(session).get_by_id(tenant_id)
            if tenant is None:
                raise TenantBillingEngineError(f"Tenant not found: {tenant_id}")

            subscription = await TenantSubscriptionRepository(session).get_by_tenant(tenant_id)
            if subscription is None:
                raise TenantBillingEngineError("Tenant subscription not found")

            start, end = period_start, period_end
            if start is None or end is None:
                start = subscription.current_period_start
                end = subscription.current_period_end

            line_defs = await TenantBillingEngineV1._build_invoice_lines(
                session,
                tenant_id=tenant_id,
                plan_code=subscription.plan_code,
                period_start=start,
                period_end=end,
            )
            subtotal = TenantBillingEngineV1._quantize(
                sum(line["amount"] for line in line_defs)
            )
            tax = TenantBillingEngineV1._quantize(subtotal * TAX_RATE)
            total = TenantBillingEngineV1._quantize(subtotal + tax)

            now = datetime.now(timezone.utc)
            prefix = f"INV-{tenant.code}-{start.strftime('%Y%m')}-"
            seq = await TenantInvoiceRepository(session).count_for_period_prefix(prefix) + 1
            invoice_number = f"{prefix}{seq:04d}"

            invoice = await TenantInvoiceRepository(session).create(
                tenant_id=tenant_id,
                company_id=tenant.company_id,
                invoice_number=invoice_number,
                period_start=start,
                period_end=end,
                currency=subscription.currency,
                subtotal=subtotal,
                tax=tax,
                total=total,
                issued_at=now,
                due_at=now + timedelta(days=14),
                generated_by=actor_id,
                metadata={
                    "plan_code": subscription.plan_code,
                    "tenant_code": tenant.code,
                    "tenant_name": tenant.name,
                },
            )

            line_repo = TenantInvoiceLineRepository(session)
            created_lines = []
            for line_def in line_defs:
                created_lines.append(
                    await line_repo.create(
                        invoice_id=invoice.id,
                        line_type=line_def["line_type"],
                        description=line_def["description"],
                        quantity=line_def["quantity"],
                        unit_price=line_def["unit_price"],
                        amount=line_def["amount"],
                    )
                )

            await TenantUsageRepository(session).attach_to_invoice(
                tenant_id,
                invoice.id,
                period_start=start,
                period_end=end,
            )

            document = TenantBillingEngineV1._invoice_document(
                tenant_name=tenant.name,
                tenant_code=tenant.code,
                invoice_number=invoice_number,
                period_start=start,
                period_end=end,
                currency=subscription.currency,
                lines=created_lines,
                subtotal=subtotal,
                tax=tax,
                total=total,
            )
            invoice.metadata_ = {**(invoice.metadata_ or {}), "document": document}

            await TenantBillingEngineV1._audit(
                session,
                actor_id=actor_id,
                action=AuditAction.EXPORT.value,
                entity_id=str(invoice.id),
                company_id=tenant.company_id,
                tenant_id=tenant_id,
                new_value={"invoice_number": invoice_number, "total": str(total)},
            )

            return TenantBillingEngineV1._invoice_snapshot(invoice, created_lines)

    @staticmethod
    def _invoice_document(
        *,
        tenant_name: str,
        tenant_code: str,
        invoice_number: str,
        period_start: date,
        period_end: date,
        currency: str,
        lines: list,
        subtotal: Decimal,
        tax: Decimal,
        total: Decimal,
    ) -> dict[str, Any]:
        return {
            "title": f"Invoice {invoice_number}",
            "tenant_name": tenant_name,
            "tenant_code": tenant_code,
            "invoice_number": invoice_number,
            "period": f"{period_start.isoformat()} — {period_end.isoformat()}",
            "currency": currency,
            "lines": [
                {
                    "description": line.description,
                    "quantity": str(line.quantity),
                    "unit_price": str(line.unit_price),
                    "amount": str(line.amount),
                }
                for line in lines
            ],
            "subtotal": str(subtotal),
            "tax": str(tax),
            "total": str(total),
        }

    @staticmethod
    async def list_invoices(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
        async with get_session() as session:
            rows = await TenantInvoiceRepository(session).list_by_tenant(tenant_id, limit=limit)
            return [TenantBillingEngineV1._invoice_snapshot(row) for row in rows]

    @staticmethod
    async def get_invoice(
        actor_id: int,
        tenant_id: uuid.UUID,
        invoice_id: uuid.UUID,
    ) -> dict[str, Any]:
        await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
        async with get_session() as session:
            invoice = await TenantInvoiceRepository(session).get_by_id(invoice_id)
            if invoice is None or invoice.tenant_id != tenant_id:
                raise TenantBillingEngineError(f"Invoice not found: {invoice_id}")
            lines = await TenantInvoiceLineRepository(session).list_by_invoice(invoice_id)
            return TenantBillingEngineV1._invoice_snapshot(invoice, lines)

    @staticmethod
    async def run_monthly_billing(*, actor_id: int | None = None) -> dict[str, Any]:
        actor = actor_id or OWNER_ID
        generated: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []

        async with get_session() as session:
            subscriptions = await TenantSubscriptionRepository(session).list_active()

        for subscription in subscriptions:
            try:
                await TenantBillingEngineV1.collect_tenant_usage(actor, subscription.tenant_id)
                invoice = await TenantBillingEngineV1.generate_invoice(
                    actor,
                    subscription.tenant_id,
                )
                generated.append({
                    "tenant_id": str(subscription.tenant_id),
                    "invoice_number": invoice["invoice_number"],
                    "total": invoice["total"],
                })
            except Exception as exc:
                errors.append({
                    "tenant_id": str(subscription.tenant_id),
                    "error": str(exc),
                })

        return {"generated": generated, "errors": errors, "count": len(generated)}
