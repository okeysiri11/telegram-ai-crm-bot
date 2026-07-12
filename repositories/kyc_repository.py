# KYC Engine repository — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.kyc import (
    KycDocument,
    KycDocumentStatus,
    KycDocumentType,
    KycProfile,
    KycProfileStatus,
    RiskLevel,
    RiskProfile,
    SanctionsCheck,
    SanctionsCheckStatus,
    SanctionsCheckType,
    VerificationLevel,
)


class KycRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_profile(
        self,
        *,
        user_id: int,
        full_name: str | None = None,
        country: str | None = None,
        date_of_birth: date | None = None,
        verification_level: str = VerificationLevel.NONE.value,
        status: str = KycProfileStatus.PENDING.value,
        **extra: Any,
    ) -> KycProfile:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if verification_level not in {v.value for v in VerificationLevel}:
            raise ValueError(f"Invalid verification_level: {verification_level}")
        if status not in {s.value for s in KycProfileStatus}:
            raise ValueError(f"Invalid status: {status}")

        profile = KycProfile(
            user_id=user_id,
            full_name=full_name,
            country=country,
            date_of_birth=date_of_birth,
            verification_level=verification_level,
            status=status,
        )
        self._session.add(profile)
        await self._session.flush()
        return profile

    async def get_profile(self, profile_id: uuid.UUID) -> KycProfile | None:
        result = await self._session.execute(
            select(KycProfile).where(KycProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def get_profile_by_user(self, user_id: int) -> KycProfile | None:
        result = await self._session.execute(
            select(KycProfile).where(KycProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_verification_level(
        self,
        profile_id: uuid.UUID,
        verification_level: str,
    ) -> KycProfile | None:
        if verification_level not in {v.value for v in VerificationLevel}:
            raise ValueError(f"Invalid verification_level: {verification_level}")

        profile = await self.get_profile(profile_id)
        if profile is None:
            return None

        profile.verification_level = verification_level
        if verification_level != VerificationLevel.NONE.value:
            profile.status = KycProfileStatus.IN_REVIEW.value
        await self._session.flush()
        return profile

    async def verify_profile(
        self,
        profile_id: uuid.UUID,
        *,
        verification_level: str,
        expires_at: datetime | None = None,
    ) -> KycProfile | None:
        profile = await self.get_profile(profile_id)
        if profile is None:
            return None

        profile.verification_level = verification_level
        profile.status = KycProfileStatus.VERIFIED.value
        profile.verified_at = datetime.now(timezone.utc)
        profile.expires_at = expires_at
        await self._session.flush()
        return profile

    async def create_document(
        self,
        *,
        profile_id: uuid.UUID,
        document_type: str,
        document_number: str | None = None,
        issuing_country: str | None = None,
        issued_at: date | None = None,
        expires_at: date | None = None,
        storage_ref: str | None = None,
        metadata: dict[str, Any] | None = None,
        **extra: Any,
    ) -> KycDocument:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if document_type not in {d.value for d in KycDocumentType}:
            raise ValueError(f"Invalid document_type: {document_type}")

        document = KycDocument(
            profile_id=profile_id,
            document_type=document_type,
            document_number=document_number,
            issuing_country=issuing_country,
            issued_at=issued_at,
            expires_at=expires_at,
            storage_ref=storage_ref,
            metadata_=metadata,
        )
        self._session.add(document)
        await self._session.flush()
        return document

    async def get_document(self, document_id: uuid.UUID) -> KycDocument | None:
        result = await self._session.execute(
            select(KycDocument).where(KycDocument.id == document_id)
        )
        return result.scalar_one_or_none()

    async def list_documents(self, profile_id: uuid.UUID) -> list[KycDocument]:
        result = await self._session.execute(
            select(KycDocument)
            .where(KycDocument.profile_id == profile_id)
            .order_by(KycDocument.created_at.asc())
        )
        return list(result.scalars().all())

    async def verify_document(self, document_id: uuid.UUID) -> KycDocument | None:
        document = await self.get_document(document_id)
        if document is None:
            return None

        document.status = KycDocumentStatus.VERIFIED.value
        document.verified_at = datetime.now(timezone.utc)
        await self._session.flush()
        return document

    async def mark_document_expired(self, document_id: uuid.UUID) -> KycDocument | None:
        document = await self.get_document(document_id)
        if document is None:
            return None

        document.status = KycDocumentStatus.EXPIRED.value
        await self._session.flush()
        return document

    async def list_expiring_documents(
        self,
        *,
        within_days: int = 30,
        limit: int = 100,
    ) -> list[KycDocument]:
        today = date.today()
        deadline = today + timedelta(days=within_days)
        result = await self._session.execute(
            select(KycDocument)
            .where(
                KycDocument.expires_at.is_not(None),
                KycDocument.expires_at <= deadline,
                KycDocument.expires_at >= today,
                KycDocument.status.in_(
                    {
                        KycDocumentStatus.PENDING.value,
                        KycDocumentStatus.VERIFIED.value,
                    }
                ),
            )
            .order_by(KycDocument.expires_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_expired_documents(self, *, limit: int = 100) -> list[KycDocument]:
        today = date.today()
        result = await self._session.execute(
            select(KycDocument)
            .where(
                KycDocument.expires_at.is_not(None),
                KycDocument.expires_at < today,
                KycDocument.status != KycDocumentStatus.EXPIRED.value,
            )
            .order_by(KycDocument.expires_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_sanctions_check(
        self,
        *,
        profile_id: uuid.UUID,
        check_type: str,
        status: str = SanctionsCheckStatus.PENDING.value,
        provider: str | None = None,
        reference: str | None = None,
        **extra: Any,
    ) -> SanctionsCheck:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if check_type not in {c.value for c in SanctionsCheckType}:
            raise ValueError(f"Invalid check_type: {check_type}")
        if status not in {s.value for s in SanctionsCheckStatus}:
            raise ValueError(f"Invalid status: {status}")

        check = SanctionsCheck(
            profile_id=profile_id,
            check_type=check_type,
            status=status,
            provider=provider,
            reference=reference,
        )
        self._session.add(check)
        await self._session.flush()
        return check

    async def complete_sanctions_check(
        self,
        check_id: uuid.UUID,
        *,
        status: str,
        match_score: Decimal | None = None,
        matched_entities: list[Any] | None = None,
        next_check_at: datetime | None = None,
        error_message: str | None = None,
    ) -> SanctionsCheck | None:
        result = await self._session.execute(
            select(SanctionsCheck).where(SanctionsCheck.id == check_id)
        )
        check = result.scalar_one_or_none()
        if check is None:
            return None
        if status not in {s.value for s in SanctionsCheckStatus}:
            raise ValueError(f"Invalid status: {status}")

        check.status = status
        check.match_score = match_score
        check.matched_entities = matched_entities
        check.checked_at = datetime.now(timezone.utc)
        check.next_check_at = next_check_at
        check.error_message = error_message
        await self._session.flush()
        return check

    async def list_sanctions_checks(self, profile_id: uuid.UUID) -> list[SanctionsCheck]:
        result = await self._session.execute(
            select(SanctionsCheck)
            .where(SanctionsCheck.profile_id == profile_id)
            .order_by(SanctionsCheck.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_or_create_risk_profile(self, profile_id: uuid.UUID) -> RiskProfile:
        result = await self._session.execute(
            select(RiskProfile).where(RiskProfile.profile_id == profile_id)
        )
        risk = result.scalar_one_or_none()
        if risk is not None:
            return risk

        risk = RiskProfile(profile_id=profile_id, aml_flags=[])
        self._session.add(risk)
        await self._session.flush()
        return risk

    async def get_risk_profile(self, profile_id: uuid.UUID) -> RiskProfile | None:
        result = await self._session.execute(
            select(RiskProfile).where(RiskProfile.profile_id == profile_id)
        )
        return result.scalar_one_or_none()

    async def add_aml_flag(
        self,
        profile_id: uuid.UUID,
        flag: str,
        *,
        recalculate: bool = True,
    ) -> RiskProfile:
        risk = await self.get_or_create_risk_profile(profile_id)
        flags = list(risk.aml_flags or [])
        if flag not in flags:
            flags.append(flag)
        risk.aml_flags = flags
        if recalculate:
            self._recalculate_risk(risk)
        await self._session.flush()
        return risk

    async def remove_aml_flag(self, profile_id: uuid.UUID, flag: str) -> RiskProfile | None:
        risk = await self.get_risk_profile(profile_id)
        if risk is None:
            return None

        flags = [item for item in (risk.aml_flags or []) if item != flag]
        risk.aml_flags = flags
        self._recalculate_risk(risk)
        await self._session.flush()
        return risk

    async def update_risk_profile(
        self,
        profile_id: uuid.UUID,
        *,
        pep_status: bool | None = None,
        sanctions_hit: bool | None = None,
        adverse_media: bool | None = None,
        source_of_funds_verified: bool | None = None,
        notes: str | None = None,
    ) -> RiskProfile:
        risk = await self.get_or_create_risk_profile(profile_id)
        if pep_status is not None:
            risk.pep_status = pep_status
        if sanctions_hit is not None:
            risk.sanctions_hit = sanctions_hit
        if adverse_media is not None:
            risk.adverse_media = adverse_media
        if source_of_funds_verified is not None:
            risk.source_of_funds_verified = source_of_funds_verified
        if notes is not None:
            risk.notes = notes
        self._recalculate_risk(risk)
        risk.last_reviewed_at = datetime.now(timezone.utc)
        await self._session.flush()
        return risk

    @staticmethod
    def _recalculate_risk(risk: RiskProfile) -> None:
        score = 0
        if risk.pep_status:
            score += 25
        if risk.sanctions_hit:
            score += 50
        if risk.adverse_media:
            score += 20
        if not risk.source_of_funds_verified:
            score += 10
        score += min(len(risk.aml_flags or []) * 5, 25)
        score = min(score, 100)

        if score >= 75:
            level = RiskLevel.CRITICAL.value
        elif score >= 50:
            level = RiskLevel.HIGH.value
        elif score >= 25:
            level = RiskLevel.MEDIUM.value
        else:
            level = RiskLevel.LOW.value

        risk.risk_score = score
        risk.risk_level = level

    async def count_profiles_by_level(self) -> dict[str, int]:
        result = await self._session.execute(
            select(KycProfile.verification_level, func.count())
            .group_by(KycProfile.verification_level)
        )
        return {row[0]: int(row[1]) for row in result.all()}
