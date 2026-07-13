# Revenue Sharing Engine v1 — partner revenue models, reports, settlements.

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import func, select

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.lead_automation_engine import AutomationLead
from database.models.partner_tenant_engine import TenantResourceType
from database.models.revenue_sharing_engine import (
    REVENUE_SHARE_MODELS,
    AgreementStatus,
    ReportStatus,
    RevenueShareModel,
    SettlementStatus,
)
from database.models.sales_pipeline_automation_engine import PipelineLead, PipelineStage
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.partner_tenant_repository import TenantResourceBindingRepository
from repositories.revenue_sharing_repository import (
    RevenueShareAgreementRepository,
    RevenueShareCalculationRepository,
    RevenueShareReportRepository,
    RevenueShareSettlementRepository,
)
from repositories.user_role_repository import UserRoleRepository
from services.pg_partner_tenant_engine import (
    PartnerTenantEngineV1,
    TenantAccessDeniedError,
)

MONEY = Decimal("0.01")
REVENUE_SHARING_ROLES = frozenset({"OWNER", "ADMIN", "ACCOUNTANT", "MANAGER"})


class RevenueSharingEngineError(Exception):
    pass


class RevenueSharingEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in REVENUE_SHARING_ROLES for role in roles)

    @staticmethod
    def _quantize(amount: Decimal) -> Decimal:
        return amount.quantize(MONEY, rounding=ROUND_HALF_UP)

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
    def _agreement_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "company_id": str(row.company_id),
            "partner_ref": row.partner_ref,
            "partner_name": row.partner_name,
            "model_type": row.model_type,
            "currency": row.currency,
            "status": row.status,
            "terms": row.terms,
            "metadata": row.metadata_ or {},
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _calculation_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "agreement_id": str(row.agreement_id),
            "period_start": row.period_start.isoformat(),
            "period_end": row.period_end.isoformat(),
            "metrics": row.metrics,
            "breakdown": row.breakdown,
            "total_amount": str(row.total_amount),
        }

    @staticmethod
    def _report_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "agreement_id": str(row.agreement_id),
            "calculation_id": str(row.calculation_id),
            "report_month": row.report_month.isoformat(),
            "status": row.status,
            "summary": row.summary,
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _settlement_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "agreement_id": str(row.agreement_id),
            "report_id": str(row.report_id),
            "amount": str(row.amount),
            "currency": row.currency,
            "status": row.status,
            "reference": row.reference,
            "notes": row.notes,
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    async def create_agreement(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        partner_ref: str,
        partner_name: str,
        model_type: str,
        terms: dict[str, Any],
        currency: str = "USD",
    ) -> dict[str, Any]:
        if not await RevenueSharingEngineV1.user_can_access(actor_id):
            raise TenantAccessDeniedError("Revenue sharing access denied")
        if model_type not in REVENUE_SHARE_MODELS:
            raise RevenueSharingEngineError(f"Invalid model_type: {model_type}")

        ctx = await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
        RevenueSharingEngineV1._validate_terms(model_type, terms)

        async with get_session() as session:
            repo = RevenueShareAgreementRepository(session)
            if await repo.get_by_partner(tenant_id, partner_ref) is not None:
                raise RevenueSharingEngineError(f"Agreement exists for partner: {partner_ref}")

            row = await repo.create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                partner_ref=partner_ref,
                partner_name=partner_name,
                model_type=model_type,
                terms=terms,
                currency=currency,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="revenue_share_agreement",
                entity_id=str(row.id),
                action=AuditAction.CREATE.value,
                new_value=RevenueSharingEngineV1._agreement_snapshot(row),
            )
            return RevenueSharingEngineV1._agreement_snapshot(row)

    @staticmethod
    def _validate_terms(model_type: str, terms: dict[str, Any]) -> None:
        if model_type == RevenueShareModel.FIXED_SUBSCRIPTION.value:
            if "monthly_amount" not in terms:
                raise RevenueSharingEngineError("terms.monthly_amount required")
        elif model_type == RevenueShareModel.PER_LEAD.value:
            if "per_lead_rate" not in terms:
                raise RevenueSharingEngineError("terms.per_lead_rate required")
        elif model_type == RevenueShareModel.REVENUE_SHARE.value:
            if "share_percent" not in terms:
                raise RevenueSharingEngineError("terms.share_percent required")
        elif model_type == RevenueShareModel.HYBRID.value:
            required_any = {"monthly_amount", "per_lead_rate", "share_percent"}
            if not required_any.intersection(terms.keys()):
                raise RevenueSharingEngineError("Hybrid terms need at least one component")

    @staticmethod
    async def _collect_metrics(
        session,
        *,
        tenant_id: uuid.UUID,
        period_start: date,
        period_end: date,
    ) -> dict[str, Any]:
        leads = await TenantResourceBindingRepository(session).list_by_tenant(
            tenant_id,
            resource_type=TenantResourceType.LEAD.value,
        )
        lead_count = len(leads)

        automation_count = lead_count
        try:
            lead_ids = [uuid.UUID(l.resource_id) for l in leads if l.resource_id]
            if lead_ids:
                result = await session.execute(
                    select(func.count())
                    .select_from(AutomationLead)
                    .where(
                        AutomationLead.id.in_(lead_ids),
                        AutomationLead.is_duplicate.is_(False),
                        func.date(AutomationLead.created_at) >= period_start,
                        func.date(AutomationLead.created_at) <= period_end,
                    )
                )
                automation_count = int(result.scalar_one() or 0)
        except ValueError:
            pass

        sold_result = await session.execute(
            select(func.count())
            .select_from(PipelineLead)
            .where(
                PipelineLead.stage == PipelineStage.SOLD.value,
                func.date(PipelineLead.updated_at) >= period_start,
                func.date(PipelineLead.updated_at) <= period_end,
            )
        )
        sold_count = int(sold_result.scalar_one() or 0)

        revenue_amount = Decimal(str(sold_count * 1000))
        effective_leads = max(lead_count, automation_count)

        return {
            "lead_count": effective_leads,
            "sold_count": sold_count,
            "revenue_amount": str(revenue_amount),
        }

    @staticmethod
    def _calculate_amounts(
        model_type: str,
        terms: dict[str, Any],
        metrics: dict[str, Any],
    ) -> tuple[dict[str, Any], Decimal]:
        breakdown: dict[str, Any] = {}
        total = Decimal("0")
        lead_count = int(metrics.get("lead_count", 0))
        revenue_amount = Decimal(str(metrics.get("revenue_amount", "0")))
        sold_count = int(metrics.get("sold_count", 0))

        def _add_component(key: str, amount: Decimal, detail: dict) -> None:
            nonlocal total
            if amount <= 0:
                return
            q = RevenueSharingEngineV1._quantize(amount)
            breakdown[key] = {**detail, "amount": str(q)}
            total += q

        if model_type in {
            RevenueShareModel.FIXED_SUBSCRIPTION.value,
            RevenueShareModel.HYBRID.value,
        } and "monthly_amount" in terms:
            _add_component(
                "fixed_subscription",
                Decimal(str(terms["monthly_amount"])),
                {"model": "FIXED_SUBSCRIPTION"},
            )

        if model_type in {
            RevenueShareModel.PER_LEAD.value,
            RevenueShareModel.HYBRID.value,
        } and "per_lead_rate" in terms:
            included = int(terms.get("included_leads", 0))
            billable = max(0, lead_count - included)
            rate = Decimal(str(terms["per_lead_rate"]))
            _add_component(
                "per_lead",
                rate * Decimal(billable),
                {
                    "model": "PER_LEAD",
                    "lead_count": lead_count,
                    "billable_leads": billable,
                    "rate": str(rate),
                },
            )

        if model_type in {
            RevenueShareModel.REVENUE_SHARE.value,
            RevenueShareModel.HYBRID.value,
        } and "share_percent" in terms:
            percent = Decimal(str(terms["share_percent"]))
            share = revenue_amount * percent / Decimal("100")
            _add_component(
                "revenue_share",
                share,
                {
                    "model": "REVENUE_SHARE",
                    "revenue_amount": str(revenue_amount),
                    "share_percent": str(percent),
                    "sold_count": sold_count,
                },
            )

        return breakdown, RevenueSharingEngineV1._quantize(total)

    @staticmethod
    async def calculate_period(
        actor_id: int,
        agreement_id: uuid.UUID,
        *,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> dict[str, Any]:
        if not await RevenueSharingEngineV1.user_can_access(actor_id):
            raise TenantAccessDeniedError("Revenue sharing access denied")

        async with get_session() as session:
            agreement = await RevenueShareAgreementRepository(session).get_by_id(agreement_id)
            if agreement is None:
                raise RevenueSharingEngineError(f"Agreement not found: {agreement_id}")
            if agreement.status != AgreementStatus.ACTIVE.value:
                raise RevenueSharingEngineError("Agreement is not active")

            start, end = period_start, period_end
            if start is None or end is None:
                start, end = RevenueSharingEngineV1._month_period()

            metrics = await RevenueSharingEngineV1._collect_metrics(
                session,
                tenant_id=agreement.tenant_id,
                period_start=start,
                period_end=end,
            )
            breakdown, total = RevenueSharingEngineV1._calculate_amounts(
                agreement.model_type,
                agreement.terms,
                metrics,
            )

            calc = await RevenueShareCalculationRepository(session).upsert(
                agreement_id=agreement.id,
                period_start=start,
                period_end=end,
                metrics=metrics,
                breakdown=breakdown,
                total_amount=total,
            )
            return RevenueSharingEngineV1._calculation_snapshot(calc)

    @staticmethod
    async def generate_monthly_report(
        actor_id: int,
        agreement_id: uuid.UUID,
        *,
        report_month: date | None = None,
    ) -> dict[str, Any]:
        month = report_month or RevenueSharingEngineV1._month_period()[0]
        period_start, period_end = RevenueSharingEngineV1._month_period(month)

        calculation = await RevenueSharingEngineV1.calculate_period(
            actor_id,
            agreement_id,
            period_start=period_start,
            period_end=period_end,
        )

        async with get_session() as session:
            agreement = await RevenueShareAgreementRepository(session).get_by_id(agreement_id)
            if agreement is None:
                raise RevenueSharingEngineError(f"Agreement not found: {agreement_id}")

            summary = {
                "partner_ref": agreement.partner_ref,
                "partner_name": agreement.partner_name,
                "model_type": agreement.model_type,
                "currency": agreement.currency,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "metrics": calculation["metrics"],
                "breakdown": calculation["breakdown"],
                "total_amount": calculation["total_amount"],
            }

            report = await RevenueShareReportRepository(session).upsert(
                agreement_id=agreement_id,
                calculation_id=uuid.UUID(calculation["id"]),
                report_month=month,
                summary=summary,
                status=ReportStatus.GENERATED.value,
            )
            return RevenueSharingEngineV1._report_snapshot(report)

    @staticmethod
    async def create_settlement(
        actor_id: int,
        agreement_id: uuid.UUID,
        report_id: uuid.UUID,
        *,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await RevenueSharingEngineV1.user_can_access(actor_id):
            raise TenantAccessDeniedError("Revenue sharing access denied")

        async with get_session() as session:
            agreement = await RevenueShareAgreementRepository(session).get_by_id(agreement_id)
            report = await RevenueShareReportRepository(session).get_by_id(report_id)
            if agreement is None or report is None:
                raise RevenueSharingEngineError("Agreement or report not found")
            if report.agreement_id != agreement_id:
                raise RevenueSharingEngineError("Report does not belong to agreement")

            amount = Decimal(str(report.summary.get("total_amount", "0")))
            settlement = await RevenueShareSettlementRepository(session).create(
                agreement_id=agreement_id,
                report_id=report_id,
                amount=amount,
                currency=agreement.currency,
                notes=notes,
                metadata={"report_month": report.report_month.isoformat()},
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=agreement.company_id,
                tenant_id=agreement.tenant_id,
                entity_type="revenue_share_settlement",
                entity_id=str(settlement.id),
                action=AuditAction.CREATE.value,
                new_value=RevenueSharingEngineV1._settlement_snapshot(settlement),
            )
            return RevenueSharingEngineV1._settlement_snapshot(settlement)

    @staticmethod
    async def mark_settlement_paid(
        actor_id: int,
        settlement_id: uuid.UUID,
        *,
        reference: str | None = None,
    ) -> dict[str, Any]:
        if not await RevenueSharingEngineV1.user_can_access(actor_id):
            raise TenantAccessDeniedError("Revenue sharing access denied")

        async with get_session() as session:
            settlement = await RevenueShareSettlementRepository(session).get_by_id(settlement_id)
            if settlement is None:
                raise RevenueSharingEngineError(f"Settlement not found: {settlement_id}")

            await RevenueShareSettlementRepository(session).mark_paid(
                settlement,
                reference=reference,
            )
            await session.refresh(settlement)
            return RevenueSharingEngineV1._settlement_snapshot(settlement)

    @staticmethod
    async def get_partner_dashboard(
        actor_id: int,
        tenant_id: uuid.UUID,
        partner_ref: str,
    ) -> dict[str, Any]:
        await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

        async with get_session() as session:
            agreement = await RevenueShareAgreementRepository(session).get_by_partner(
                tenant_id,
                partner_ref,
            )
            if agreement is None:
                raise RevenueSharingEngineError(f"No agreement for partner: {partner_ref}")

            reports = await RevenueShareReportRepository(session).list_by_agreement(
                agreement.id,
                limit=12,
            )
            settlements = await RevenueShareSettlementRepository(session).list_by_agreement(
                agreement.id,
                limit=12,
            )

            total_paid = sum(
                (Decimal(str(s.amount)) for s in settlements if s.status == SettlementStatus.PAID.value),
                Decimal("0"),
            )
            total_pending = sum(
                (Decimal(str(s.amount)) for s in settlements if s.status == SettlementStatus.PENDING.value),
                Decimal("0"),
            )
            latest_report = reports[0] if reports else None

            return {
                "agreement": RevenueSharingEngineV1._agreement_snapshot(agreement),
                "latest_report": RevenueSharingEngineV1._report_snapshot(latest_report)
                if latest_report
                else None,
                "reports": [RevenueSharingEngineV1._report_snapshot(r) for r in reports],
                "settlements": [
                    RevenueSharingEngineV1._settlement_snapshot(s) for s in settlements
                ],
                "totals": {
                    "paid": str(RevenueSharingEngineV1._quantize(total_paid)),
                    "pending": str(RevenueSharingEngineV1._quantize(total_pending)),
                    "currency": agreement.currency,
                },
            }

    @staticmethod
    async def list_agreements(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
        async with get_session() as session:
            rows = await RevenueShareAgreementRepository(session).list_by_tenant(
                tenant_id,
                limit=limit,
            )
            return [RevenueSharingEngineV1._agreement_snapshot(r) for r in rows]

    @staticmethod
    async def run_monthly_cycle(*, actor_id: int | None = None) -> dict[str, Any]:
        actor = actor_id or OWNER_ID
        generated: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []

        async with get_session() as session:
            agreements = await RevenueShareAgreementRepository(session).list_active()

        for agreement in agreements:
            try:
                report = await RevenueSharingEngineV1.generate_monthly_report(
                    actor,
                    agreement.id,
                )
                settlement = await RevenueSharingEngineV1.create_settlement(
                    actor,
                    agreement.id,
                    uuid.UUID(report["id"]),
                )
                generated.append({
                    "partner_ref": agreement.partner_ref,
                    "report_id": report["id"],
                    "settlement_id": settlement["id"],
                    "amount": settlement["amount"],
                })
            except Exception as exc:
                errors.append({
                    "partner_ref": agreement.partner_ref,
                    "error": str(exc),
                })

        return {"generated": generated, "errors": errors, "count": len(generated)}

    @staticmethod
    async def list_models() -> list[dict[str, str]]:
        labels = {
            RevenueShareModel.FIXED_SUBSCRIPTION.value: "Fixed Subscription",
            RevenueShareModel.PER_LEAD.value: "Per Lead",
            RevenueShareModel.REVENUE_SHARE.value: "Revenue Share",
            RevenueShareModel.HYBRID.value: "Hybrid",
        }
        return [
            {"code": code, "label": labels.get(code, code)}
            for code in sorted(REVENUE_SHARE_MODELS)
        ]
