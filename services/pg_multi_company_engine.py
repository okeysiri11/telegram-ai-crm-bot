# Multi Company Engine v1 — legal entities, branches, intercompany, consolidation.

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from config import OWNER_ID
from database.models.multi_company import (
    ConsolidatedReportStatus,
    ConsolidatedReportType,
    IntercompanyTransactionStatus,
    IntercompanyTransactionType,
)
from database.session import get_session
from repositories.automotive_inventory_repository import VehicleRepository
from repositories.multi_company_repository import (
    BranchRepository,
    CompanyRepository,
    ConsolidatedReportRepository,
    IntercompanyTransactionRepository,
)
from repositories.user_role_repository import UserRoleRepository

MULTI_COMPANY_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER", "ACCOUNTANT"})
MONEY = Decimal("0.01")


class MultiCompanyEngineError(Exception):
    pass


class MultiCompanyEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in MULTI_COMPANY_ROLES for role in roles)

    @staticmethod
    def _quantize(amount: Decimal) -> Decimal:
        return amount.quantize(MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    def _company_snapshot(company) -> dict[str, Any]:
        return {
            "id": str(company.id),
            "code": company.code,
            "legal_name": company.legal_name,
            "tax_id": company.tax_id,
            "currency": company.currency,
            "country": company.country,
            "accounting_prefix": company.accounting_prefix,
            "is_active": company.is_active,
            "settings": company.settings,
            "created_at": company.created_at.isoformat(),
        }

    @staticmethod
    def _branch_snapshot(branch) -> dict[str, Any]:
        return {
            "id": str(branch.id),
            "company_id": str(branch.company_id),
            "code": branch.code,
            "name": branch.name,
            "address": branch.address,
            "country": branch.country,
            "region": branch.region,
            "shared_inventory": branch.shared_inventory,
            "is_active": branch.is_active,
        }

    @staticmethod
    def _transaction_snapshot(txn) -> dict[str, Any]:
        return {
            "id": str(txn.id),
            "from_company_id": str(txn.from_company_id),
            "to_company_id": str(txn.to_company_id),
            "from_branch_id": str(txn.from_branch_id) if txn.from_branch_id else None,
            "to_branch_id": str(txn.to_branch_id) if txn.to_branch_id else None,
            "transaction_type": txn.transaction_type,
            "amount": str(txn.amount),
            "currency": txn.currency,
            "reference": txn.reference,
            "status": txn.status,
            "vehicle_id": str(txn.vehicle_id) if txn.vehicle_id else None,
            "created_at": txn.created_at.isoformat(),
        }

    @staticmethod
    def _report_snapshot(report) -> dict[str, Any]:
        return {
            "id": str(report.id),
            "report_type": report.report_type,
            "period_start": report.period_start.isoformat(),
            "period_end": report.period_end.isoformat(),
            "companies_included": report.companies_included,
            "data": report.data,
            "currency": report.currency,
            "status": report.status,
            "generated_by": report.generated_by,
            "created_at": report.created_at.isoformat(),
        }

    @staticmethod
    async def create_company(
        actor_id: int,
        *,
        code: str,
        legal_name: str,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await MultiCompanyEngineV1.user_can_access(actor_id):
            raise MultiCompanyEngineError("Access denied")

        async with get_session() as session:
            if await CompanyRepository(session).get_by_code(code):
                raise MultiCompanyEngineError(f"Company already exists: {code}")
            company = await CompanyRepository(session).create(
                code=code,
                legal_name=legal_name,
                **fields,
            )
            return MultiCompanyEngineV1._company_snapshot(company)

    @staticmethod
    async def create_branch(
        actor_id: int,
        company_id: uuid.UUID,
        *,
        code: str,
        name: str,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await MultiCompanyEngineV1.user_can_access(actor_id):
            raise MultiCompanyEngineError("Access denied")

        async with get_session() as session:
            company = await CompanyRepository(session).get_by_id(company_id)
            if company is None:
                raise MultiCompanyEngineError(f"Company not found: {company_id}")
            if await BranchRepository(session).get_by_code(company_id, code):
                raise MultiCompanyEngineError(f"Branch already exists: {code}")

            branch = await BranchRepository(session).create(
                company_id=company_id,
                code=code,
                name=name,
                **fields,
            )
            return MultiCompanyEngineV1._branch_snapshot(branch)

    @staticmethod
    async def record_intercompany_transaction(
        actor_id: int,
        *,
        from_company_id: uuid.UUID,
        to_company_id: uuid.UUID,
        transaction_type: str,
        amount: Decimal,
        reference: str,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await MultiCompanyEngineV1.user_can_access(actor_id):
            raise MultiCompanyEngineError("Access denied")

        async with get_session() as session:
            company_repo = CompanyRepository(session)
            if await company_repo.get_by_id(from_company_id) is None:
                raise MultiCompanyEngineError(f"From company not found: {from_company_id}")
            if await company_repo.get_by_id(to_company_id) is None:
                raise MultiCompanyEngineError(f"To company not found: {to_company_id}")

            txn_repo = IntercompanyTransactionRepository(session)
            if await txn_repo.get_by_reference(reference):
                raise MultiCompanyEngineError(f"Reference already exists: {reference}")

            txn = await txn_repo.create(
                from_company_id=from_company_id,
                to_company_id=to_company_id,
                transaction_type=transaction_type,
                amount=MultiCompanyEngineV1._quantize(amount),
                reference=reference,
                created_by=actor_id,
                **fields,
            )
            return MultiCompanyEngineV1._transaction_snapshot(txn)

    @staticmethod
    async def settle_intercompany_transaction(
        actor_id: int,
        transaction_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await MultiCompanyEngineV1.user_can_access(actor_id):
            raise MultiCompanyEngineError("Access denied")

        async with get_session() as session:
            txn_repo = IntercompanyTransactionRepository(session)
            txn = await txn_repo.get_by_id(transaction_id)
            if txn is None:
                raise MultiCompanyEngineError(f"Transaction not found: {transaction_id}")

            txn = await txn_repo.update_status(
                transaction_id,
                IntercompanyTransactionStatus.SETTLED.value,
            )

            try:
                from services.pg_settlement_engine import SettlementEngineV1

                await SettlementEngineV1.create_settlement(
                    actor_id,
                    settlement_type="BANK",
                    asset=txn.currency,
                    amount=txn.amount,
                    reference=f"intercompany-{txn.reference}",
                )
            except Exception:
                pass

            return MultiCompanyEngineV1._transaction_snapshot(txn)

    @staticmethod
    async def assign_vehicle_to_branch(
        actor_id: int,
        vehicle_id: uuid.UUID,
        branch_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await MultiCompanyEngineV1.user_can_access(actor_id):
            raise MultiCompanyEngineError("Access denied")

        async with get_session() as session:
            branch = await BranchRepository(session).get_by_id(branch_id)
            if branch is None:
                raise MultiCompanyEngineError(f"Branch not found: {branch_id}")

            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise MultiCompanyEngineError(f"Vehicle not found: {vehicle_id}")

            company = await CompanyRepository(session).get_by_id(branch.company_id)
            note = (
                f"branch:{branch.code}|company:{company.code if company else 'unknown'}"
                f"|region:{branch.region or 'unknown'}"
            )
            existing = vehicle.notes or ""
            vehicle.notes = f"{existing} {note}".strip()
            vehicle.updated_at = datetime.now(timezone.utc)
            await session.flush()

            return {
                "vehicle_id": str(vehicle_id),
                "branch_id": str(branch_id),
                "company_id": str(branch.company_id),
                "shared_inventory": branch.shared_inventory,
            }

    @staticmethod
    async def get_company_accounting_summary(
        actor_id: int,
        company_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await MultiCompanyEngineV1.user_can_access(actor_id):
            raise MultiCompanyEngineError("Access denied")

        async with get_session() as session:
            company = await CompanyRepository(session).get_by_id(company_id)
            if company is None:
                raise MultiCompanyEngineError(f"Company not found: {company_id}")

            branches = await BranchRepository(session).list_by_company(company_id)
            txns = await IntercompanyTransactionRepository(session).list_by_company(
                company_id
            )

            inbound = sum(
                t.amount for t in txns
                if t.to_company_id == company_id and t.status == IntercompanyTransactionStatus.SETTLED.value
            )
            outbound = sum(
                t.amount for t in txns
                if t.from_company_id == company_id and t.status == IntercompanyTransactionStatus.SETTLED.value
            )

            prefix = company.accounting_prefix or company.code
            return {
                "company": MultiCompanyEngineV1._company_snapshot(company),
                "branches_count": len(branches),
                "intercompany_inbound": str(inbound),
                "intercompany_outbound": str(outbound),
                "net_intercompany": str(inbound - outbound),
                "accounting_prefix": prefix,
                "separate_accounting": True,
            }

    @staticmethod
    async def generate_consolidated_report(
        actor_id: int,
        *,
        report_type: str,
        period_start: date,
        period_end: date,
        company_ids: list[uuid.UUID] | None = None,
    ) -> dict[str, Any]:
        if not await MultiCompanyEngineV1.user_can_access(actor_id):
            raise MultiCompanyEngineError("Access denied")

        if report_type not in {t.value for t in ConsolidatedReportType}:
            raise MultiCompanyEngineError(f"Invalid report_type: {report_type}")

        async with get_session() as session:
            company_repo = CompanyRepository(session)
            if company_ids:
                companies = []
                for cid in company_ids:
                    c = await company_repo.get_by_id(cid)
                    if c:
                        companies.append(c)
            else:
                companies = await company_repo.list_active()

            company_data: list[dict[str, Any]] = []
            total_inventory_value = Decimal("0")
            total_revenue = Decimal("0")

            vehicles = await VehicleRepository(session).list_all(limit=5000)
            for company in companies:
                prefix = company.code
                company_vehicles = [
                    v for v in vehicles
                    if v.notes and prefix.lower() in v.notes.lower()
                ]
                inv_value = sum(
                    (v.purchase_price or Decimal("0")) for v in company_vehicles
                )
                revenue = sum(
                    (v.sale_price or Decimal("0")) for v in company_vehicles
                )
                total_inventory_value += inv_value
                total_revenue += revenue

                branches = await BranchRepository(session).list_by_company(company.id)
                txns = await IntercompanyTransactionRepository(session).list_by_company(
                    company.id
                )

                company_data.append({
                    "company_id": str(company.id),
                    "code": company.code,
                    "legal_name": company.legal_name,
                    "currency": company.currency,
                    "branches": len(branches),
                    "vehicle_count": len(company_vehicles),
                    "inventory_value": str(inv_value),
                    "revenue": str(revenue),
                    "intercompany_transactions": len(txns),
                })

            shared_inventory_enabled = False
            for company in companies:
                branches = await BranchRepository(session).list_by_company(company.id)
                if any(b.shared_inventory for b in branches):
                    shared_inventory_enabled = True
                    break

            report_data = {
                "report_type": report_type,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "companies": company_data,
                "totals": {
                    "inventory_value": str(total_inventory_value),
                    "revenue": str(total_revenue),
                    "companies_count": len(companies),
                },
                "shared_inventory_enabled": shared_inventory_enabled,
            }

            report = await ConsolidatedReportRepository(session).create(
                report_type=report_type,
                period_start=period_start,
                period_end=period_end,
                companies_included=[str(c.id) for c in companies],
                data=report_data,
                currency="USD",
                generated_by=actor_id,
                status=ConsolidatedReportStatus.GENERATED.value,
            )

            return MultiCompanyEngineV1._report_snapshot(report)

    @staticmethod
    async def list_companies(actor_id: int) -> list[dict[str, Any]]:
        if not await MultiCompanyEngineV1.user_can_access(actor_id):
            raise MultiCompanyEngineError("Access denied")

        async with get_session() as session:
            companies = await CompanyRepository(session).list_active()
            return [MultiCompanyEngineV1._company_snapshot(c) for c in companies]

    @staticmethod
    async def list_branches(
        actor_id: int,
        company_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        if not await MultiCompanyEngineV1.user_can_access(actor_id):
            raise MultiCompanyEngineError("Access denied")

        async with get_session() as session:
            branches = await BranchRepository(session).list_by_company(company_id)
            return [MultiCompanyEngineV1._branch_snapshot(b) for b in branches]

    @staticmethod
    async def get_consolidated_report(
        actor_id: int,
        report_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await MultiCompanyEngineV1.user_can_access(actor_id):
            raise MultiCompanyEngineError("Access denied")

        async with get_session() as session:
            report = await ConsolidatedReportRepository(session).get_by_id(report_id)
            if report is None:
                raise MultiCompanyEngineError(f"Report not found: {report_id}")
            return MultiCompanyEngineV1._report_snapshot(report)
