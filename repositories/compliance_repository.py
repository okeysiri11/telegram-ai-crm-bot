# KYC / AML Engine v1 repositories — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.compliance import (
    AmlCheckResult,
    AmlCheckType,
    ComplianceAmlCheck,
    ComplianceDocumentStatus,
    ComplianceDocumentType,
    ComplianceEntityType,
    ComplianceKycDocument,
    ComplianceKycProfile,
    ComplianceKycStatus,
    ComplianceRiskLevel,
    ComplianceRiskProfile,
    ComplianceVerificationLevel,
)


class KycProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        partner_id: uuid.UUID,
        entity_type: str,
        verification_level: str = ComplianceVerificationLevel.L0.value,
        status: str = ComplianceKycStatus.NOT_STARTED.value,
        **extra: Any,
    ) -> ComplianceKycProfile:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if entity_type not in {e.value for e in ComplianceEntityType}:
            raise ValueError(f"Invalid entity_type: {entity_type}")

        profile = ComplianceKycProfile(
            partner_id=partner_id,
            entity_type=entity_type,
            verification_level=verification_level,
            status=status,
        )
        self._session.add(profile)
        await self._session.flush()
        return profile

    async def get_by_id(self, profile_id: uuid.UUID) -> ComplianceKycProfile | None:
        result = await self._session.execute(
            select(ComplianceKycProfile).where(ComplianceKycProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def get_by_partner(self, partner_id: uuid.UUID) -> ComplianceKycProfile | None:
        result = await self._session.execute(
            select(ComplianceKycProfile).where(
                ComplianceKycProfile.partner_id == partner_id
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        *,
        partner_id: uuid.UUID,
        entity_type: str,
    ) -> ComplianceKycProfile:
        profile = await self.get_by_partner(partner_id)
        if profile is not None:
            return profile
        return await self.create(partner_id=partner_id, entity_type=entity_type)

    async def start(self, profile_id: uuid.UUID) -> ComplianceKycProfile | None:
        profile = await self.get_by_id(profile_id)
        if profile is None:
            return None
        profile.status = ComplianceKycStatus.PENDING.value
        await self._session.flush()
        return profile

    async def approve(
        self,
        profile_id: uuid.UUID,
        *,
        verification_level: str,
        expires_at: datetime | None = None,
    ) -> ComplianceKycProfile | None:
        profile = await self.get_by_id(profile_id)
        if profile is None:
            return None
        profile.status = ComplianceKycStatus.APPROVED.value
        profile.verification_level = verification_level
        profile.verified_at = datetime.now(timezone.utc)
        profile.expires_at = expires_at
        await self._session.flush()
        return profile

    async def reject(self, profile_id: uuid.UUID) -> ComplianceKycProfile | None:
        profile = await self.get_by_id(profile_id)
        if profile is None:
            return None
        profile.status = ComplianceKycStatus.REJECTED.value
        await self._session.flush()
        return profile


class KycDocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        kyc_profile_id: uuid.UUID,
        document_type: str,
        document_number: str | None = None,
        issue_country: str | None = None,
        **extra: Any,
    ) -> ComplianceKycDocument:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if document_type not in {d.value for d in ComplianceDocumentType}:
            raise ValueError(f"Invalid document_type: {document_type}")

        document = ComplianceKycDocument(
            kyc_profile_id=kyc_profile_id,
            document_type=document_type,
            document_number=document_number,
            issue_country=issue_country,
        )
        self._session.add(document)
        await self._session.flush()
        return document

    async def get_by_id(self, document_id: uuid.UUID) -> ComplianceKycDocument | None:
        result = await self._session.execute(
            select(ComplianceKycDocument).where(ComplianceKycDocument.id == document_id)
        )
        return result.scalar_one_or_none()

    async def list_by_profile(self, kyc_profile_id: uuid.UUID) -> list[ComplianceKycDocument]:
        result = await self._session.execute(
            select(ComplianceKycDocument)
            .where(ComplianceKycDocument.kyc_profile_id == kyc_profile_id)
            .order_by(ComplianceKycDocument.uploaded_at.asc())
        )
        return list(result.scalars().all())

    async def approve(self, document_id: uuid.UUID) -> ComplianceKycDocument | None:
        document = await self.get_by_id(document_id)
        if document is None:
            return None
        document.status = ComplianceDocumentStatus.APPROVED.value
        document.reviewed_at = datetime.now(timezone.utc)
        await self._session.flush()
        return document

    async def reject(self, document_id: uuid.UUID) -> ComplianceKycDocument | None:
        document = await self.get_by_id(document_id)
        if document is None:
            return None
        document.status = ComplianceDocumentStatus.REJECTED.value
        document.reviewed_at = datetime.now(timezone.utc)
        await self._session.flush()
        return document


class AmlCheckRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        partner_id: uuid.UUID,
        check_type: str,
        result: str,
        score: int | None = None,
        **extra: Any,
    ) -> ComplianceAmlCheck:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if check_type not in {c.value for c in AmlCheckType}:
            raise ValueError(f"Invalid check_type: {check_type}")
        if result not in {r.value for r in AmlCheckResult}:
            raise ValueError(f"Invalid result: {result}")

        check = ComplianceAmlCheck(
            partner_id=partner_id,
            check_type=check_type,
            result=result,
            score=score,
            checked_at=datetime.now(timezone.utc),
        )
        self._session.add(check)
        await self._session.flush()
        return check

    async def list_by_partner(self, partner_id: uuid.UUID) -> list[ComplianceAmlCheck]:
        result = await self._session.execute(
            select(ComplianceAmlCheck)
            .where(ComplianceAmlCheck.partner_id == partner_id)
            .order_by(ComplianceAmlCheck.checked_at.desc())
        )
        return list(result.scalars().all())

    async def latest_by_partner(self, partner_id: uuid.UUID) -> ComplianceAmlCheck | None:
        result = await self._session.execute(
            select(ComplianceAmlCheck)
            .where(ComplianceAmlCheck.partner_id == partner_id)
            .order_by(ComplianceAmlCheck.checked_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class RiskProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self, partner_id: uuid.UUID) -> ComplianceRiskProfile:
        result = await self._session.execute(
            select(ComplianceRiskProfile).where(
                ComplianceRiskProfile.partner_id == partner_id
            )
        )
        risk = result.scalar_one_or_none()
        if risk is not None:
            return risk

        risk = ComplianceRiskProfile(partner_id=partner_id)
        self._session.add(risk)
        await self._session.flush()
        return risk

    async def get_by_partner(self, partner_id: uuid.UUID) -> ComplianceRiskProfile | None:
        result = await self._session.execute(
            select(ComplianceRiskProfile).where(
                ComplianceRiskProfile.partner_id == partner_id
            )
        )
        return result.scalar_one_or_none()

    async def update_risk(
        self,
        partner_id: uuid.UUID,
        *,
        risk_score: int,
        notes: str | None = None,
    ) -> ComplianceRiskProfile:
        risk = await self.get_or_create(partner_id)
        risk.risk_score = max(0, min(100, risk_score))
        if notes is not None:
            risk.notes = notes

        if risk.risk_score >= 75:
            risk.risk_level = ComplianceRiskLevel.CRITICAL.value
        elif risk.risk_score >= 50:
            risk.risk_level = ComplianceRiskLevel.HIGH.value
        elif risk.risk_score >= 25:
            risk.risk_level = ComplianceRiskLevel.MEDIUM.value
        else:
            risk.risk_level = ComplianceRiskLevel.LOW.value

        await self._session.flush()
        return risk
