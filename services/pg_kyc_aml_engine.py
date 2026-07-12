# KYC / AML Engine v1 — partner-centric compliance subsystem.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.compliance import (
    AmlCheckResult,
    AmlCheckType,
    ComplianceAmlCheck,
    ComplianceKycDocument,
    ComplianceKycProfile,
    ComplianceKycStatus,
    ComplianceRiskProfile,
    ComplianceVerificationLevel,
)
from database.models.partner_engine import PartnerAmlStatus, PartnerKycStatus
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.compliance_repository import (
    AmlCheckRepository,
    KycDocumentRepository,
    KycProfileRepository,
    RiskProfileRepository,
)
from repositories.partner_engine_repositories import PartnerRepository
from repositories.user_role_repository import UserRoleRepository

COMPLIANCE_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER", "LAWYER"})


class KycAmlEngineError(Exception):
    pass


class PermissionDeniedError(KycAmlEngineError):
    pass


class KycAmlEngine:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in COMPLIANCE_ROLES for role in roles)

    @staticmethod
    async def _audit(
        session,
        *,
        user_id: int,
        action: str,
        entity_type: str,
        entity_id: str,
        old_value: dict | None = None,
        new_value: dict | None = None,
    ) -> None:
        await AuditRepository(session).create_log(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
        )

    @staticmethod
    async def _publish_event(
        event_type: str,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> None:
        try:
            from services import crm_event_bus as bus

            await bus.publish_event(
                event_type,
                aggregate_type,
                aggregate_id,
                payload,
            )
        except Exception:
            pass

    @staticmethod
    def _profile_snapshot(profile: ComplianceKycProfile) -> dict[str, Any]:
        return {
            "id": str(profile.id),
            "partner_id": str(profile.partner_id),
            "entity_type": profile.entity_type,
            "verification_level": profile.verification_level,
            "status": profile.status,
            "verified_at": profile.verified_at.isoformat() if profile.verified_at else None,
            "expires_at": profile.expires_at.isoformat() if profile.expires_at else None,
        }

    @staticmethod
    async def _sync_partner_kyc(
        session,
        partner_id: uuid.UUID,
        kyc_status: str,
        *,
        risk_level: str | None = None,
        aml_status: str | None = None,
    ) -> None:
        partner = await PartnerRepository(session).get_by_id(partner_id)
        if partner is None:
            return
        partner.kyc_status = kyc_status
        if risk_level is not None:
            partner.risk_level = risk_level
        if aml_status is not None:
            partner.aml_status = aml_status
        await session.flush()

    @staticmethod
    async def start_kyc(
        actor_id: int,
        partner_id: uuid.UUID,
        *,
        entity_type: str = "COMPANY",
    ) -> ComplianceKycProfile:
        if not await KycAmlEngine.user_can_access(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            partner = await PartnerRepository(session).get_by_id(partner_id)
            if partner is None:
                raise KycAmlEngineError(f"Partner not found: {partner_id}")

            profile = await KycProfileRepository(session).get_or_create(
                partner_id=partner_id,
                entity_type=entity_type,
            )
            profile = await KycProfileRepository(session).start(profile.id)
            if profile is None:
                raise KycAmlEngineError("Failed to start KYC profile")

            await KycAmlEngine._sync_partner_kyc(
                session,
                partner_id,
                PartnerKycStatus.PENDING.value,
            )
            await RiskProfileRepository(session).get_or_create(partner_id)

        await KycAmlEngine._publish_event(
            "kyc.started",
            "kyc",
            profile.id,
            KycAmlEngine._profile_snapshot(profile),
        )
        return profile

    @staticmethod
    async def upload_document(
        actor_id: int,
        partner_id: uuid.UUID,
        *,
        document_type: str,
        document_number: str | None = None,
        issue_country: str | None = None,
    ) -> ComplianceKycDocument:
        if not await KycAmlEngine.user_can_access(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            profile = await KycProfileRepository(session).get_by_partner(partner_id)
            if profile is None:
                raise KycAmlEngineError(f"KYC profile not found for partner: {partner_id}")

            document = await KycDocumentRepository(session).create(
                kyc_profile_id=profile.id,
                document_type=document_type,
                document_number=document_number,
                issue_country=issue_country,
            )

            await KycAmlEngine._audit(
                session,
                user_id=actor_id,
                action=AuditAction.DOCUMENT_UPLOADED.value,
                entity_type="kyc_document",
                entity_id=str(document.id),
                new_value={
                    "partner_id": str(partner_id),
                    "document_type": document_type,
                    "document_number": document_number,
                },
            )

        return document

    @staticmethod
    async def approve_kyc(
        actor_id: int,
        partner_id: uuid.UUID,
        *,
        verification_level: str = ComplianceVerificationLevel.L2.value,
        valid_for_days: int = 365,
    ) -> ComplianceKycProfile:
        if not await KycAmlEngine.user_can_access(actor_id):
            raise PermissionDeniedError("Access denied")

        expires_at = datetime.now(timezone.utc) + timedelta(days=valid_for_days)

        async with get_session() as session:
            profile_repo = KycProfileRepository(session)
            profile = await profile_repo.get_by_partner(partner_id)
            if profile is None:
                raise KycAmlEngineError(f"KYC profile not found for partner: {partner_id}")

            old_value = KycAmlEngine._profile_snapshot(profile)
            profile = await profile_repo.approve(
                profile.id,
                verification_level=verification_level,
                expires_at=expires_at,
            )
            if profile is None:
                raise KycAmlEngineError("Failed to approve KYC profile")

            await KycAmlEngine._sync_partner_kyc(
                session,
                partner_id,
                PartnerKycStatus.APPROVED.value,
            )

            await KycAmlEngine._audit(
                session,
                user_id=actor_id,
                action=AuditAction.KYC_APPROVED.value,
                entity_type="kyc",
                entity_id=str(profile.id),
                old_value=old_value,
                new_value=KycAmlEngine._profile_snapshot(profile),
            )

        await KycAmlEngine._publish_event(
            "kyc.approved",
            "kyc",
            profile.id,
            KycAmlEngine._profile_snapshot(profile),
        )
        return profile

    @staticmethod
    async def reject_kyc(
        actor_id: int,
        partner_id: uuid.UUID,
        *,
        reason: str | None = None,
    ) -> ComplianceKycProfile:
        if not await KycAmlEngine.user_can_access(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            profile_repo = KycProfileRepository(session)
            profile = await profile_repo.get_by_partner(partner_id)
            if profile is None:
                raise KycAmlEngineError(f"KYC profile not found for partner: {partner_id}")

            old_value = KycAmlEngine._profile_snapshot(profile)
            profile = await profile_repo.reject(profile.id)
            if profile is None:
                raise KycAmlEngineError("Failed to reject KYC profile")

            await KycAmlEngine._sync_partner_kyc(
                session,
                partner_id,
                PartnerKycStatus.REJECTED.value,
            )

            await KycAmlEngine._audit(
                session,
                user_id=actor_id,
                action=AuditAction.KYC_REJECTED.value,
                entity_type="kyc",
                entity_id=str(profile.id),
                old_value=old_value,
                new_value={
                    **KycAmlEngine._profile_snapshot(profile),
                    "reason": reason,
                },
            )

        payload = KycAmlEngine._profile_snapshot(profile)
        if reason:
            payload["reason"] = reason
        await KycAmlEngine._publish_event("kyc.rejected", "kyc", profile.id, payload)
        return profile

    @staticmethod
    async def run_aml_screening(
        actor_id: int,
        partner_id: uuid.UUID,
        *,
        check_types: list[str] | None = None,
    ) -> list[ComplianceAmlCheck]:
        if not await KycAmlEngine.user_can_access(actor_id):
            raise PermissionDeniedError("Access denied")

        types = check_types or [t.value for t in AmlCheckType]
        checks: list[ComplianceAmlCheck] = []
        review_required = False
        blocked = False
        max_score = 0

        async with get_session() as session:
            partner = await PartnerRepository(session).get_by_id(partner_id)
            if partner is None:
                raise KycAmlEngineError(f"Partner not found: {partner_id}")

            aml_repo = AmlCheckRepository(session)
            risk_repo = RiskProfileRepository(session)

            for check_type in types:
                # Placeholder screening — replace with external provider integration.
                result = AmlCheckResult.CLEAR.value
                score = 0

                check = await aml_repo.create(
                    partner_id=partner_id,
                    check_type=check_type,
                    result=result,
                    score=score,
                )
                checks.append(check)
                max_score = max(max_score, score or 0)

                if result == AmlCheckResult.REVIEW.value:
                    review_required = True
                elif result == AmlCheckResult.BLOCKED.value:
                    blocked = True

                await KycAmlEngine._audit(
                    session,
                    user_id=actor_id,
                    action=AuditAction.AML_FLAG_CREATED.value,
                    entity_type="aml",
                    entity_id=str(check.id),
                    new_value={
                        "partner_id": str(partner_id),
                        "check_type": check_type,
                        "result": result,
                        "score": score,
                    },
                )

            risk = await risk_repo.update_risk(
                partner_id,
                risk_score=max_score,
                notes=f"AML screening: {len(checks)} checks",
            )

            if blocked:
                await PartnerRepository(session).block(partner_id)
                await KycAmlEngine._sync_partner_kyc(
                    session,
                    partner_id,
                    partner.kyc_status,
                    risk_level=risk.risk_level,
                    aml_status=PartnerAmlStatus.BLOCKED.value,
                )
            elif review_required:
                await KycAmlEngine._sync_partner_kyc(
                    session,
                    partner_id,
                    partner.kyc_status,
                    risk_level=risk.risk_level,
                    aml_status=PartnerAmlStatus.REVIEW.value,
                )
            else:
                await KycAmlEngine._sync_partner_kyc(
                    session,
                    partner_id,
                    partner.kyc_status,
                    risk_level=risk.risk_level,
                    aml_status=PartnerAmlStatus.CLEAR.value,
                )

        if blocked:
            await KycAmlEngine._publish_event(
                "partner.blocked",
                "partner",
                partner_id,
                {"reason": "aml_blocked", "checks": len(checks)},
            )
        elif review_required:
            await KycAmlEngine._publish_event(
                "aml.review_required",
                "aml",
                partner_id,
                {"partner_id": str(partner_id), "checks": len(checks)},
            )

        return checks

    @staticmethod
    async def get_compliance_summary(
        actor_id: int,
        partner_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await KycAmlEngine.user_can_access(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            partner = await PartnerRepository(session).get_by_id(partner_id)
            if partner is None:
                raise KycAmlEngineError(f"Partner not found: {partner_id}")

            profile = await KycProfileRepository(session).get_by_partner(partner_id)
            documents = (
                await KycDocumentRepository(session).list_by_profile(profile.id)
                if profile
                else []
            )
            aml_checks = await AmlCheckRepository(session).list_by_partner(partner_id)
            risk = await RiskProfileRepository(session).get_by_partner(partner_id)

            return {
                "partner_id": str(partner_id),
                "partner_status": partner.status,
                "partner_kyc_status": partner.kyc_status,
                "partner_aml_status": partner.aml_status,
                "partner_risk_level": partner.risk_level,
                "kyc_profile": KycAmlEngine._profile_snapshot(profile) if profile else None,
                "documents": [
                    {
                        "id": str(d.id),
                        "document_type": d.document_type,
                        "status": d.status,
                        "uploaded_at": d.uploaded_at.isoformat(),
                    }
                    for d in documents
                ],
                "aml_checks": [
                    {
                        "id": str(c.id),
                        "check_type": c.check_type,
                        "result": c.result,
                        "score": c.score,
                        "checked_at": c.checked_at.isoformat(),
                    }
                    for c in aml_checks
                ],
                "risk_profile": {
                    "risk_score": risk.risk_score,
                    "risk_level": risk.risk_level,
                    "notes": risk.notes,
                }
                if risk
                else None,
            }
