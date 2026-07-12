# KYC Engine — verification levels, AML flags, sanctions screening, document expiry.

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from database.models.kyc import (
    KycDocument,
    KycDocumentStatus,
    KycProfile,
    KycProfileStatus,
    RiskProfile,
    SanctionsCheck,
    SanctionsCheckStatus,
    SanctionsCheckType,
    VerificationLevel,
)
from database.session import get_session
from repositories.kyc_repository import KycRepository


class KycEngineError(Exception):
    pass


class KycEngine:
    @staticmethod
    async def create_profile(
        *,
        user_id: int,
        full_name: str | None = None,
        country: str | None = None,
        date_of_birth: date | None = None,
    ) -> KycProfile:
        async with get_session() as session:
            repo = KycRepository(session)
            existing = await repo.get_profile_by_user(user_id)
            if existing is not None:
                return existing
            profile = await repo.create_profile(
                user_id=user_id,
                full_name=full_name,
                country=country,
                date_of_birth=date_of_birth,
            )
            await repo.get_or_create_risk_profile(profile.id)
            return profile

    @staticmethod
    async def get_profile(user_id: int) -> KycProfile | None:
        async with get_session() as session:
            return await KycRepository(session).get_profile_by_user(user_id)

    @staticmethod
    async def set_verification_level(
        profile_id: uuid.UUID,
        verification_level: str,
    ) -> KycProfile:
        async with get_session() as session:
            repo = KycRepository(session)
            profile = await repo.update_verification_level(profile_id, verification_level)
            if profile is None:
                raise KycEngineError(f"Profile not found: {profile_id}")
            return profile

    @staticmethod
    async def verify_profile(
        profile_id: uuid.UUID,
        *,
        verification_level: str = VerificationLevel.STANDARD.value,
        valid_for_days: int = 365,
    ) -> KycProfile:
        expires_at = datetime.now(timezone.utc) + timedelta(days=valid_for_days)
        async with get_session() as session:
            repo = KycRepository(session)
            profile = await repo.verify_profile(
                profile_id,
                verification_level=verification_level,
                expires_at=expires_at,
            )
            if profile is None:
                raise KycEngineError(f"Profile not found: {profile_id}")
            return profile

    @staticmethod
    async def add_document(
        *,
        profile_id: uuid.UUID,
        document_type: str,
        document_number: str | None = None,
        issuing_country: str | None = None,
        issued_at: date | None = None,
        expires_at: date | None = None,
        storage_ref: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> KycDocument:
        async with get_session() as session:
            repo = KycRepository(session)
            profile = await repo.get_profile(profile_id)
            if profile is None:
                raise KycEngineError(f"Profile not found: {profile_id}")
            return await repo.create_document(
                profile_id=profile_id,
                document_type=document_type,
                document_number=document_number,
                issuing_country=issuing_country,
                issued_at=issued_at,
                expires_at=expires_at,
                storage_ref=storage_ref,
                metadata=metadata,
            )

    @staticmethod
    async def verify_document(document_id: uuid.UUID) -> KycDocument:
        async with get_session() as session:
            repo = KycRepository(session)
            document = await repo.verify_document(document_id)
            if document is None:
                raise KycEngineError(f"Document not found: {document_id}")
            return document

    @staticmethod
    async def track_expiring_documents(*, within_days: int = 30) -> list[KycDocument]:
        async with get_session() as session:
            return await KycRepository(session).list_expiring_documents(
                within_days=within_days
            )

    @staticmethod
    async def process_expired_documents() -> list[KycDocument]:
        async with get_session() as session:
            repo = KycRepository(session)
            expired = await repo.list_expired_documents()
            processed: list[KycDocument] = []
            for document in expired:
                updated = await repo.mark_document_expired(document.id)
                if updated is not None:
                    processed.append(updated)
            return processed

    @staticmethod
    async def run_sanctions_screening(
        profile_id: uuid.UUID,
        *,
        check_types: list[str] | None = None,
        provider: str = "internal",
    ) -> list[SanctionsCheck]:
        types = check_types or [t.value for t in SanctionsCheckType]
        async with get_session() as session:
            repo = KycRepository(session)
            profile = await repo.get_profile(profile_id)
            if profile is None:
                raise KycEngineError(f"Profile not found: {profile_id}")

            checks: list[SanctionsCheck] = []
            sanctions_hit = False
            for check_type in types:
                pending = await repo.create_sanctions_check(
                    profile_id=profile_id,
                    check_type=check_type,
                    provider=provider,
                )
                # Placeholder screening — real provider integration would go here.
                status = SanctionsCheckStatus.CLEAR.value
                matched: list[Any] = []
                score: Decimal | None = None

                completed = await repo.complete_sanctions_check(
                    pending.id,
                    status=status,
                    match_score=score,
                    matched_entities=matched or None,
                    next_check_at=datetime.now(timezone.utc) + timedelta(days=90),
                )
                if completed is not None:
                    checks.append(completed)
                    if completed.status == SanctionsCheckStatus.MATCH.value:
                        sanctions_hit = True

            risk = await repo.update_risk_profile(
                profile_id,
                sanctions_hit=sanctions_hit,
            )
            if sanctions_hit:
                await repo.add_aml_flag(profile_id, "SANCTIONS_MATCH", recalculate=True)
                profile.status = KycProfileStatus.SUSPENDED.value
                await session.flush()
            elif risk.risk_level in {"HIGH", "CRITICAL"}:
                profile.status = KycProfileStatus.IN_REVIEW.value
                await session.flush()

            return checks

    @staticmethod
    async def add_aml_flag(profile_id: uuid.UUID, flag: str) -> RiskProfile:
        async with get_session() as session:
            repo = KycRepository(session)
            profile = await repo.get_profile(profile_id)
            if profile is None:
                raise KycEngineError(f"Profile not found: {profile_id}")
            risk = await repo.add_aml_flag(profile_id, flag)
            if risk.risk_level in {"HIGH", "CRITICAL"}:
                profile.status = KycProfileStatus.IN_REVIEW.value
                await session.flush()
            return risk

    @staticmethod
    async def remove_aml_flag(profile_id: uuid.UUID, flag: str) -> RiskProfile:
        async with get_session() as session:
            repo = KycRepository(session)
            risk = await repo.remove_aml_flag(profile_id, flag)
            if risk is None:
                raise KycEngineError(f"Risk profile not found: {profile_id}")
            return risk

    @staticmethod
    async def get_risk_profile(profile_id: uuid.UUID) -> RiskProfile:
        async with get_session() as session:
            repo = KycRepository(session)
            risk = await repo.get_risk_profile(profile_id)
            if risk is None:
                raise KycEngineError(f"Risk profile not found: {profile_id}")
            return risk

    @staticmethod
    async def update_risk_indicators(
        profile_id: uuid.UUID,
        *,
        pep_status: bool | None = None,
        adverse_media: bool | None = None,
        source_of_funds_verified: bool | None = None,
    ) -> RiskProfile:
        async with get_session() as session:
            repo = KycRepository(session)
            profile = await repo.get_profile(profile_id)
            if profile is None:
                raise KycEngineError(f"Profile not found: {profile_id}")
            risk = await repo.update_risk_profile(
                profile_id,
                pep_status=pep_status,
                adverse_media=adverse_media,
                source_of_funds_verified=source_of_funds_verified,
            )
            if pep_status:
                await repo.add_aml_flag(profile_id, "PEP", recalculate=False)
                repo._recalculate_risk(risk)
                await session.flush()
            if risk.risk_level in {"HIGH", "CRITICAL"}:
                profile.status = KycProfileStatus.IN_REVIEW.value
                await session.flush()
            return risk

    @staticmethod
    async def get_compliance_summary(profile_id: uuid.UUID) -> dict[str, Any]:
        async with get_session() as session:
            repo = KycRepository(session)
            profile = await repo.get_profile(profile_id)
            if profile is None:
                raise KycEngineError(f"Profile not found: {profile_id}")

            documents = await repo.list_documents(profile_id)
            checks = await repo.list_sanctions_checks(profile_id)
            risk = await repo.get_risk_profile(profile_id)
            expiring = [
                doc for doc in documents
                if doc.expires_at is not None
                and doc.status in {
                    KycDocumentStatus.PENDING.value,
                    KycDocumentStatus.VERIFIED.value,
                }
                and doc.expires_at <= date.today() + timedelta(days=30)
            ]

            return {
                "profile_id": str(profile_id),
                "user_id": profile.user_id,
                "verification_level": profile.verification_level,
                "status": profile.status,
                "verified_at": profile.verified_at.isoformat() if profile.verified_at else None,
                "expires_at": profile.expires_at.isoformat() if profile.expires_at else None,
                "document_count": len(documents),
                "expiring_documents": len(expiring),
                "sanctions_checks": len(checks),
                "latest_sanctions_status": checks[0].status if checks else None,
                "risk_level": risk.risk_level if risk else None,
                "risk_score": risk.risk_score if risk else None,
                "aml_flags": list(risk.aml_flags) if risk else [],
            }
