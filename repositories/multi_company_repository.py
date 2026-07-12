# Multi Company Engine v1 repositories.

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.multi_company import (
    Branch,
    Company,
    ConsolidatedReport,
    ConsolidatedReportStatus,
    IntercompanyTransaction,
    IntercompanyTransactionStatus,
    IntercompanyTransactionType,
)


class CompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        code: str,
        legal_name: str,
        currency: str = "USD",
        tax_id: str | None = None,
        country: str | None = None,
        accounting_prefix: str | None = None,
        is_active: bool = True,
        settings: dict | None = None,
        **extra: Any,
    ) -> Company:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        company = Company(
            code=code,
            legal_name=legal_name,
            currency=currency,
            tax_id=tax_id,
            country=country,
            accounting_prefix=accounting_prefix,
            is_active=is_active,
            settings=settings,
        )
        self._session.add(company)
        await self._session.flush()
        return company

    async def get_by_id(self, company_id: uuid.UUID) -> Company | None:
        result = await self._session.execute(
            select(Company).where(Company.id == company_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Company | None:
        result = await self._session.execute(
            select(Company).where(Company.code == code)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Company]:
        result = await self._session.execute(
            select(Company)
            .where(Company.is_active.is_(True))
            .order_by(Company.code.asc())
        )
        return list(result.scalars().all())


class BranchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        code: str,
        name: str,
        address: str | None = None,
        country: str | None = None,
        region: str | None = None,
        shared_inventory: bool = True,
        is_active: bool = True,
        **extra: Any,
    ) -> Branch:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        branch = Branch(
            company_id=company_id,
            code=code,
            name=name,
            address=address,
            country=country,
            region=region,
            shared_inventory=shared_inventory,
            is_active=is_active,
        )
        self._session.add(branch)
        await self._session.flush()
        return branch

    async def get_by_id(self, branch_id: uuid.UUID) -> Branch | None:
        result = await self._session.execute(
            select(Branch).where(Branch.id == branch_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(
        self,
        company_id: uuid.UUID,
        code: str,
    ) -> Branch | None:
        result = await self._session.execute(
            select(Branch).where(
                Branch.company_id == company_id,
                Branch.code == code,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_company(self, company_id: uuid.UUID) -> list[Branch]:
        result = await self._session.execute(
            select(Branch)
            .where(Branch.company_id == company_id, Branch.is_active.is_(True))
            .order_by(Branch.code.asc())
        )
        return list(result.scalars().all())


class IntercompanyTransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        from_company_id: uuid.UUID,
        to_company_id: uuid.UUID,
        transaction_type: str,
        amount: Decimal,
        reference: str,
        currency: str = "USD",
        **fields: Any,
    ) -> IntercompanyTransaction:
        if transaction_type not in {t.value for t in IntercompanyTransactionType}:
            raise ValueError(f"Invalid transaction_type: {transaction_type}")

        txn = IntercompanyTransaction(
            from_company_id=from_company_id,
            to_company_id=to_company_id,
            transaction_type=transaction_type,
            amount=amount,
            reference=reference,
            currency=currency,
            **fields,
        )
        self._session.add(txn)
        await self._session.flush()
        return txn

    async def get_by_id(self, transaction_id: uuid.UUID) -> IntercompanyTransaction | None:
        result = await self._session.execute(
            select(IntercompanyTransaction).where(
                IntercompanyTransaction.id == transaction_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_reference(self, reference: str) -> IntercompanyTransaction | None:
        result = await self._session.execute(
            select(IntercompanyTransaction).where(
                IntercompanyTransaction.reference == reference
            )
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        transaction_id: uuid.UUID,
        status: str,
    ) -> IntercompanyTransaction | None:
        txn = await self.get_by_id(transaction_id)
        if txn is None:
            return None
        if status not in {s.value for s in IntercompanyTransactionStatus}:
            raise ValueError(f"Invalid status: {status}")
        txn.status = status
        txn.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return txn

    async def list_by_company(
        self,
        company_id: uuid.UUID,
        *,
        limit: int = 100,
    ) -> list[IntercompanyTransaction]:
        result = await self._session.execute(
            select(IntercompanyTransaction)
            .where(
                (IntercompanyTransaction.from_company_id == company_id)
                | (IntercompanyTransaction.to_company_id == company_id)
            )
            .order_by(IntercompanyTransaction.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class ConsolidatedReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        report_type: str,
        period_start: date,
        period_end: date,
        companies_included: list[str] | None = None,
        data: dict | None = None,
        currency: str = "USD",
        generated_by: int | None = None,
        **fields: Any,
    ) -> ConsolidatedReport:
        report = ConsolidatedReport(
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            companies_included=companies_included,
            data=data,
            currency=currency,
            generated_by=generated_by,
            **fields,
        )
        self._session.add(report)
        await self._session.flush()
        return report

    async def get_by_id(self, report_id: uuid.UUID) -> ConsolidatedReport | None:
        result = await self._session.execute(
            select(ConsolidatedReport).where(ConsolidatedReport.id == report_id)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        report_id: uuid.UUID,
        status: str,
        *,
        data: dict | None = None,
    ) -> ConsolidatedReport | None:
        report = await self.get_by_id(report_id)
        if report is None:
            return None
        if status not in {s.value for s in ConsolidatedReportStatus}:
            raise ValueError(f"Invalid status: {status}")
        report.status = status
        if data is not None:
            report.data = data
        report.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return report

    async def list_recent(self, *, limit: int = 50) -> list[ConsolidatedReport]:
        result = await self._session.execute(
            select(ConsolidatedReport)
            .order_by(ConsolidatedReport.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
