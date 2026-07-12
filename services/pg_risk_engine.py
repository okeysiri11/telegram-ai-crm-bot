# Risk Engine v1 — centralized risk evaluation subsystem.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.compliance import (
    AmlCheckResult,
    ComplianceKycStatus,
    ComplianceVerificationLevel,
)
from database.models.partner_engine import PartnerAmlStatus, PartnerKycStatus, PartnerStatus
from database.models.risk import (
    RiskDecision,
    RiskDecisionResult,
    RiskEvaluationType,
    RiskLevel,
    RiskRuleType,
)
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.compliance_repository import (
    AmlCheckRepository,
    KycProfileRepository,
    RiskProfileRepository,
)
from repositories.deal_repository import DealRepository
from repositories.partner_engine_repositories import PartnerLimitRepository, PartnerRepository
from repositories.risk_repository import (
    BlockedOperationRepository,
    ExposureLimitRepository,
    RiskDecisionRepository,
    RiskEventRepository,
    RiskRuleRepository,
)
from repositories.user_role_repository import UserRoleRepository

RISK_READ_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER", "LAWYER", "ACCOUNTANT"})
RISK_WRITE_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER", "LAWYER"})

RISK_LEVEL_RANK = {
    RiskLevel.LOW.value: 0,
    RiskLevel.MEDIUM.value: 1,
    RiskLevel.HIGH.value: 2,
    RiskLevel.CRITICAL.value: 3,
}

DECISION_RANK = {
    RiskDecisionResult.APPROVED.value: 0,
    RiskDecisionResult.REVIEW_REQUIRED.value: 1,
    RiskDecisionResult.OWNER_APPROVAL_REQUIRED.value: 2,
    RiskDecisionResult.REJECTED.value: 3,
}

DEFAULT_BLOCKED_COUNTRIES = frozenset({"KP", "IR", "SY", "CU", "RU-CRIMEA"})
KYC_LEVEL_RANK = {
    ComplianceVerificationLevel.L0.value: 0,
    ComplianceVerificationLevel.L1.value: 1,
    ComplianceVerificationLevel.L2.value: 2,
    ComplianceVerificationLevel.L3.value: 3,
    ComplianceVerificationLevel.L4.value: 4,
}


class RiskEngineError(Exception):
    pass


class RiskEngineV1:
    @staticmethod
    async def user_can_read(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in RISK_READ_ROLES for role in roles)

    @staticmethod
    async def user_can_write(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in RISK_WRITE_ROLES for role in roles)

    @staticmethod
    async def _audit(
        session,
        *,
        user_id: int,
        action: str,
        entity_id: str,
        old_value: dict | None = None,
        new_value: dict | None = None,
    ) -> None:
        await AuditRepository(session).create_log(
            user_id=user_id,
            entity_type="risk",
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
        )

    @staticmethod
    async def _publish_event(
        event_type: str,
        aggregate_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> None:
        try:
            from services import crm_event_bus as bus

            await bus.publish_event(
                event_type,
                "risk",
                aggregate_id,
                payload,
            )
        except Exception:
            pass

    @staticmethod
    def _max_risk_level(levels: list[str]) -> str:
        if not levels:
            return RiskLevel.LOW.value
        return max(levels, key=lambda level: RISK_LEVEL_RANK.get(level, 0))

    @staticmethod
    def _resolve_decision(checks: list[dict[str, Any]]) -> str:
        decision = RiskDecisionResult.APPROVED.value
        for check in checks:
            hinted = check.get("decision_hint")
            if hinted and DECISION_RANK.get(hinted, 0) > DECISION_RANK[decision]:
                decision = hinted
                continue
            level = check.get("risk_level", RiskLevel.LOW.value)
            if check.get("passed") is False:
                if level == RiskLevel.CRITICAL.value:
                    if check.get("rule_type") in {
                        RiskRuleType.SANCTIONS_RISK.value,
                        RiskRuleType.COUNTRY_RISK.value,
                    }:
                        decision = RiskDecisionResult.REJECTED.value
                    elif DECISION_RANK[decision] < DECISION_RANK[
                        RiskDecisionResult.OWNER_APPROVAL_REQUIRED.value
                    ]:
                        decision = RiskDecisionResult.OWNER_APPROVAL_REQUIRED.value
                elif level == RiskLevel.HIGH.value:
                    if DECISION_RANK[decision] < DECISION_RANK[
                        RiskDecisionResult.REVIEW_REQUIRED.value
                    ]:
                        decision = RiskDecisionResult.REVIEW_REQUIRED.value
                elif level == RiskLevel.MEDIUM.value:
                    if decision == RiskDecisionResult.APPROVED.value:
                        decision = RiskDecisionResult.REVIEW_REQUIRED.value
        return decision

    @staticmethod
    async def _record_events_and_blocks(
        session,
        *,
        actor_id: int,
        decision: RiskDecision,
        checks: list[dict[str, Any]],
    ) -> None:
        event_repo = RiskEventRepository(session)
        blocked_repo = BlockedOperationRepository(session)

        for check in checks:
            if check.get("passed") is True:
                continue

            await event_repo.create(
                event_type=check.get("check_type", "risk.check"),
                risk_level=check.get("risk_level", RiskLevel.MEDIUM.value),
                message=check.get("message", "Risk check failed"),
                deal_id=decision.deal_id,
                partner_id=decision.partner_id,
                source_type=decision.evaluation_type,
                source_id=str(decision.id),
                details=check,
            )

            if decision.decision == RiskDecisionResult.REJECTED.value:
                await blocked_repo.create(
                    decision_id=decision.id,
                    operation_type=check.get("operation_type", "DEAL"),
                    subject_type=decision.evaluation_type,
                    subject_id=str(decision.deal_id or decision.partner_id),
                    reason=check.get("message", "Risk rejection"),
                    rule_code=check.get("rule_code"),
                )

    @staticmethod
    async def _finalize_evaluation(
        actor_id: int,
        *,
        evaluation_type: str,
        checks: list[dict[str, Any]],
        deal_id: uuid.UUID | None = None,
        partner_id: uuid.UUID | None = None,
        asset: str | None = None,
        amount: Decimal | None = None,
    ) -> dict[str, Any]:
        risk_level = RiskEngineV1._max_risk_level(
            [check.get("risk_level", RiskLevel.LOW.value) for check in checks]
        )
        decision_result = RiskEngineV1._resolve_decision(checks)

        async with get_session() as session:
            decision = await RiskDecisionRepository(session).create(
                evaluation_type=evaluation_type,
                risk_level=risk_level,
                decision=decision_result,
                checks=checks,
                deal_id=deal_id,
                partner_id=partner_id,
                asset=asset,
                amount=amount,
                decided_by=actor_id,
            )
            await RiskEngineV1._record_events_and_blocks(
                session,
                actor_id=actor_id,
                decision=decision,
                checks=checks,
            )
            await RiskEngineV1._audit(
                session,
                user_id=actor_id,
                action=AuditAction.RISK_CHECK.value,
                entity_id=str(decision.id),
                new_value={
                    "evaluation_type": evaluation_type,
                    "decision": decision_result,
                    "risk_level": risk_level,
                    "checks_count": len(checks),
                },
            )

            if decision_result == RiskDecisionResult.REJECTED.value:
                await RiskEngineV1._audit(
                    session,
                    user_id=actor_id,
                    action=AuditAction.RISK_REJECTION.value,
                    entity_id=str(decision.id),
                    new_value={"checks": checks},
                )

        aggregate_id = deal_id or partner_id or decision.id

        failed_checks = [c for c in checks if not c.get("passed")]
        if failed_checks:
            await RiskEngineV1._publish_event(
                "risk.detected",
                aggregate_id,
                {
                    "decision_id": str(decision.id),
                    "risk_level": risk_level,
                    "failed_checks": len(failed_checks),
                },
            )

        if decision_result == RiskDecisionResult.REVIEW_REQUIRED.value:
            await RiskEngineV1._publish_event(
                "risk.review_required",
                aggregate_id,
                {"decision_id": str(decision.id), "risk_level": risk_level},
            )
        elif decision_result == RiskDecisionResult.APPROVED.value:
            await RiskEngineV1._publish_event(
                "risk.approved",
                aggregate_id,
                {"decision_id": str(decision.id), "risk_level": risk_level},
            )
        elif decision_result == RiskDecisionResult.REJECTED.value:
            await RiskEngineV1._publish_event(
                "risk.rejected",
                aggregate_id,
                {"decision_id": str(decision.id), "risk_level": risk_level},
            )

        return {
            "decision_id": str(decision.id),
            "evaluation_type": evaluation_type,
            "risk_level": risk_level,
            "decision": decision_result,
            "checks": checks,
        }

    @staticmethod
    async def _check_transaction_amount(
        session,
        amount: Decimal,
        *,
        deal_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        rules = await RiskRuleRepository(session).list_active(
            RiskRuleType.TRANSACTION_RISK.value
        )
        for rule in rules:
            threshold = rule.threshold
            if threshold is not None and amount > threshold:
                return {
                    "check_type": "deal_amount_limit",
                    "rule_type": RiskRuleType.TRANSACTION_RISK.value,
                    "rule_code": rule.rule_code,
                    "passed": False,
                    "risk_level": rule.risk_level,
                    "message": (
                        f"Deal amount {amount} exceeds limit {threshold} "
                        f"({rule.rule_code})"
                    ),
                    "amount": str(amount),
                    "threshold": str(threshold),
                    "deal_id": str(deal_id) if deal_id else None,
                    "operation_type": "DEAL",
                }
        return {
            "check_type": "deal_amount_limit",
            "rule_type": RiskRuleType.TRANSACTION_RISK.value,
            "passed": True,
            "risk_level": RiskLevel.LOW.value,
            "message": "Deal amount within limits",
            "amount": str(amount),
        }

    @staticmethod
    async def _check_partner_limits(
        session,
        partner_id: uuid.UUID,
        amount: Decimal,
    ) -> dict[str, Any]:
        limit = await PartnerLimitRepository(session).get_by_partner(partner_id)
        if limit is None:
            return {
                "check_type": "partner_limits",
                "rule_type": RiskRuleType.PARTNER_RISK.value,
                "passed": True,
                "risk_level": RiskLevel.LOW.value,
                "message": "No partner limits configured",
            }

        daily_remaining = limit.daily_limit - limit.current_daily_volume
        monthly_remaining = limit.monthly_limit - limit.current_monthly_volume
        if limit.daily_limit > 0 and amount > daily_remaining:
            return {
                "check_type": "partner_limits",
                "rule_type": RiskRuleType.PARTNER_RISK.value,
                "rule_code": "partner.daily_limit",
                "passed": False,
                "risk_level": RiskLevel.HIGH.value,
                "decision_hint": RiskDecisionResult.REVIEW_REQUIRED.value,
                "message": (
                    f"Partner daily limit exceeded: "
                    f"{limit.current_daily_volume + amount} > {limit.daily_limit}"
                ),
                "operation_type": "DEAL",
            }
        if limit.monthly_limit > 0 and amount > monthly_remaining:
            return {
                "check_type": "partner_limits",
                "rule_type": RiskRuleType.PARTNER_RISK.value,
                "rule_code": "partner.monthly_limit",
                "passed": False,
                "risk_level": RiskLevel.HIGH.value,
                "decision_hint": RiskDecisionResult.REVIEW_REQUIRED.value,
                "message": (
                    f"Partner monthly limit exceeded: "
                    f"{limit.current_monthly_volume + amount} > {limit.monthly_limit}"
                ),
                "operation_type": "DEAL",
            }
        return {
            "check_type": "partner_limits",
            "rule_type": RiskRuleType.PARTNER_RISK.value,
            "passed": True,
            "risk_level": RiskLevel.LOW.value,
            "message": "Partner limits OK",
        }

    @staticmethod
    async def _check_partner_profile(session, partner_id: uuid.UUID) -> list[dict[str, Any]]:
        partner = await PartnerRepository(session).get_by_id(partner_id)
        if partner is None:
            return [
                {
                    "check_type": "partner_exists",
                    "rule_type": RiskRuleType.PARTNER_RISK.value,
                    "passed": False,
                    "risk_level": RiskLevel.CRITICAL.value,
                    "decision_hint": RiskDecisionResult.REJECTED.value,
                    "message": f"Partner not found: {partner_id}",
                    "operation_type": "DEAL",
                }
            ]

        checks: list[dict[str, Any]] = []

        if partner.status == PartnerStatus.BLOCKED.value:
            checks.append(
                {
                    "check_type": "partner_status",
                    "rule_type": RiskRuleType.PARTNER_RISK.value,
                    "passed": False,
                    "risk_level": RiskLevel.CRITICAL.value,
                    "decision_hint": RiskDecisionResult.REJECTED.value,
                    "message": "Partner is blocked",
                    "operation_type": "DEAL",
                }
            )
        elif partner.status == PartnerStatus.SUSPENDED.value:
            checks.append(
                {
                    "check_type": "partner_status",
                    "rule_type": RiskRuleType.PARTNER_RISK.value,
                    "passed": False,
                    "risk_level": RiskLevel.HIGH.value,
                    "decision_hint": RiskDecisionResult.REVIEW_REQUIRED.value,
                    "message": "Partner is suspended",
                    "operation_type": "DEAL",
                }
            )
        else:
            checks.append(
                {
                    "check_type": "partner_status",
                    "rule_type": RiskRuleType.PARTNER_RISK.value,
                    "passed": True,
                    "risk_level": RiskLevel.LOW.value,
                    "message": f"Partner status: {partner.status}",
                }
            )

        partner_risk = partner.risk_level
        if partner_risk in {RiskLevel.CRITICAL.value, RiskLevel.HIGH.value}:
            checks.append(
                {
                    "check_type": "partner_risk_score",
                    "rule_type": RiskRuleType.PARTNER_RISK.value,
                    "passed": False,
                    "risk_level": partner_risk,
                    "decision_hint": (
                        RiskDecisionResult.OWNER_APPROVAL_REQUIRED.value
                        if partner_risk == RiskLevel.CRITICAL.value
                        else RiskDecisionResult.REVIEW_REQUIRED.value
                    ),
                    "message": f"Partner risk level: {partner_risk}",
                    "operation_type": "DEAL",
                }
            )
        else:
            risk_profile = await RiskProfileRepository(session).get_by_partner(partner_id)
            score = risk_profile.risk_score if risk_profile else 0
            checks.append(
                {
                    "check_type": "partner_risk_score",
                    "rule_type": RiskRuleType.PARTNER_RISK.value,
                    "passed": True,
                    "risk_level": partner_risk,
                    "message": f"Partner risk score: {score}",
                    "risk_score": score,
                }
            )

        return checks

    @staticmethod
    async def _check_kyc(session, partner_id: uuid.UUID, amount: Decimal) -> dict[str, Any]:
        partner = await PartnerRepository(session).get_by_id(partner_id)
        kyc_profile = await KycProfileRepository(session).get_by_partner(partner_id)

        required_level = ComplianceVerificationLevel.L1.value
        rules = await RiskRuleRepository(session).list_active(RiskRuleType.KYC_RISK.value)
        for rule in rules:
            threshold = rule.threshold
            config = rule.config or {}
            if threshold is not None and amount >= threshold:
                required_level = config.get("min_level", ComplianceVerificationLevel.L2.value)

        if partner and partner.kyc_status == PartnerKycStatus.REJECTED.value:
            return {
                "check_type": "kyc_validation",
                "rule_type": RiskRuleType.KYC_RISK.value,
                "passed": False,
                "risk_level": RiskLevel.CRITICAL.value,
                "decision_hint": RiskDecisionResult.REJECTED.value,
                "message": "Partner KYC rejected",
                "operation_type": "DEAL",
            }

        actual_level = (
            kyc_profile.verification_level
            if kyc_profile
            else ComplianceVerificationLevel.L0.value
        )
        actual_status = (
            kyc_profile.status if kyc_profile else ComplianceKycStatus.NOT_STARTED.value
        )

        if actual_status != ComplianceKycStatus.APPROVED.value:
            return {
                "check_type": "kyc_validation",
                "rule_type": RiskRuleType.KYC_RISK.value,
                "passed": False,
                "risk_level": RiskLevel.HIGH.value,
                "decision_hint": RiskDecisionResult.REVIEW_REQUIRED.value,
                "message": f"KYC not approved (status={actual_status})",
                "required_level": required_level,
                "actual_level": actual_level,
                "operation_type": "DEAL",
            }

        if KYC_LEVEL_RANK.get(actual_level, 0) < KYC_LEVEL_RANK.get(required_level, 0):
            return {
                "check_type": "kyc_validation",
                "rule_type": RiskRuleType.KYC_RISK.value,
                "passed": False,
                "risk_level": RiskLevel.HIGH.value,
                "decision_hint": RiskDecisionResult.REVIEW_REQUIRED.value,
                "message": (
                    f"KYC level {actual_level} below required {required_level} "
                    f"for amount {amount}"
                ),
                "required_level": required_level,
                "actual_level": actual_level,
                "operation_type": "DEAL",
            }

        return {
            "check_type": "kyc_validation",
            "rule_type": RiskRuleType.KYC_RISK.value,
            "passed": True,
            "risk_level": RiskLevel.LOW.value,
            "message": f"KYC level {actual_level} approved",
            "actual_level": actual_level,
        }

    @staticmethod
    async def _check_country(session, partner_id: uuid.UUID) -> dict[str, Any]:
        partner = await PartnerRepository(session).get_by_id(partner_id)
        if partner is None or not partner.country:
            return {
                "check_type": "country_restriction",
                "rule_type": RiskRuleType.COUNTRY_RISK.value,
                "passed": True,
                "risk_level": RiskLevel.LOW.value,
                "message": "No country restriction",
            }

        country = partner.country.upper()
        blocked = DEFAULT_BLOCKED_COUNTRIES

        rules = await RiskRuleRepository(session).list_active(
            RiskRuleType.COUNTRY_RISK.value
        )
        for rule in rules:
            config = rule.config or {}
            blocked = blocked | frozenset(config.get("blocked_countries", []))

        if country in blocked:
            return {
                "check_type": "country_restriction",
                "rule_type": RiskRuleType.COUNTRY_RISK.value,
                "rule_code": "country.blocked",
                "passed": False,
                "risk_level": RiskLevel.CRITICAL.value,
                "decision_hint": RiskDecisionResult.REJECTED.value,
                "message": f"Country {country} is restricted",
                "country": country,
                "operation_type": "DEAL",
            }

        return {
            "check_type": "country_restriction",
            "rule_type": RiskRuleType.COUNTRY_RISK.value,
            "passed": True,
            "risk_level": RiskLevel.LOW.value,
            "message": f"Country {country} allowed",
            "country": country,
        }

    @staticmethod
    async def _check_sanctions(session, partner_id: uuid.UUID) -> dict[str, Any]:
        partner = await PartnerRepository(session).get_by_id(partner_id)
        if partner and partner.aml_status == PartnerAmlStatus.BLOCKED.value:
            return {
                "check_type": "sanctions_restriction",
                "rule_type": RiskRuleType.SANCTIONS_RISK.value,
                "passed": False,
                "risk_level": RiskLevel.CRITICAL.value,
                "decision_hint": RiskDecisionResult.REJECTED.value,
                "message": "Partner AML status is BLOCKED",
                "operation_type": "DEAL",
            }

        latest = await AmlCheckRepository(session).latest_by_partner(partner_id)
        if latest and latest.result == AmlCheckResult.BLOCKED.value:
            return {
                "check_type": "sanctions_restriction",
                "rule_type": RiskRuleType.SANCTIONS_RISK.value,
                "passed": False,
                "risk_level": RiskLevel.CRITICAL.value,
                "decision_hint": RiskDecisionResult.REJECTED.value,
                "message": f"AML check {latest.check_type} result BLOCKED",
                "operation_type": "DEAL",
            }
        if latest and latest.result == AmlCheckResult.REVIEW.value:
            return {
                "check_type": "sanctions_restriction",
                "rule_type": RiskRuleType.SANCTIONS_RISK.value,
                "passed": False,
                "risk_level": RiskLevel.HIGH.value,
                "decision_hint": RiskDecisionResult.REVIEW_REQUIRED.value,
                "message": f"AML check {latest.check_type} requires review",
                "operation_type": "DEAL",
            }

        return {
            "check_type": "sanctions_restriction",
            "rule_type": RiskRuleType.SANCTIONS_RISK.value,
            "passed": True,
            "risk_level": RiskLevel.LOW.value,
            "message": "Sanctions screening clear",
        }

    @staticmethod
    async def _check_concentration(
        session,
        *,
        partner_id: uuid.UUID | None,
        asset: str | None,
        amount: Decimal,
    ) -> dict[str, Any]:
        exposure_repo = ExposureLimitRepository(session)
        candidates = []

        global_limit = await exposure_repo.get_matching(scope="GLOBAL")
        if global_limit:
            candidates.append(global_limit)
        if asset:
            asset_limit = await exposure_repo.get_matching(scope="ASSET", scope_key=asset)
            if asset_limit:
                candidates.append(asset_limit)
        if partner_id:
            partner_limit = await exposure_repo.get_matching(
                scope="PARTNER",
                scope_key=str(partner_id),
            )
            if partner_limit:
                candidates.append(partner_limit)

        for limit in candidates:
            projected = limit.current_exposure + amount
            if projected > limit.max_exposure:
                utilization = (
                    float(projected / limit.max_exposure * 100)
                    if limit.max_exposure
                    else 100.0
                )
                return {
                    "check_type": "exposure_concentration",
                    "rule_type": RiskRuleType.CONCENTRATION_RISK.value,
                    "passed": False,
                    "risk_level": (
                        RiskLevel.CRITICAL.value
                        if utilization >= 100
                        else RiskLevel.HIGH.value
                    ),
                    "decision_hint": RiskDecisionResult.OWNER_APPROVAL_REQUIRED.value,
                    "message": (
                        f"Exposure limit exceeded for {limit.scope}/"
                        f"{limit.scope_key or '*'}: "
                        f"{projected} > {limit.max_exposure}"
                    ),
                    "scope": limit.scope,
                    "scope_key": limit.scope_key,
                    "operation_type": "DEAL",
                }

        return {
            "check_type": "exposure_concentration",
            "rule_type": RiskRuleType.CONCENTRATION_RISK.value,
            "passed": True,
            "risk_level": RiskLevel.LOW.value,
            "message": "Exposure concentration within limits",
        }

    @staticmethod
    async def evaluate_deal_risk(
        actor_id: int,
        deal_id: uuid.UUID,
        *,
        partner_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        if not await RiskEngineV1.user_can_read(actor_id):
            raise RiskEngineError("Access denied")

        async with get_session() as session:
            deal = await DealRepository(session).get_by_id(deal_id)
            if deal is None:
                raise RiskEngineError(f"Deal not found: {deal_id}")

            amount = deal.asset_out_amount or deal.asset_in_amount or Decimal("0")
            asset = deal.asset_out_type or deal.asset_in_type

            checks: list[dict[str, Any]] = []
            checks.append(
                await RiskEngineV1._check_transaction_amount(
                    session, amount, deal_id=deal_id
                )
            )

            if partner_id is not None:
                checks.extend(await RiskEngineV1._check_partner_profile(session, partner_id))
                checks.append(
                    await RiskEngineV1._check_partner_limits(session, partner_id, amount)
                )
                checks.append(await RiskEngineV1._check_kyc(session, partner_id, amount))
                checks.append(await RiskEngineV1._check_country(session, partner_id))
                checks.append(await RiskEngineV1._check_sanctions(session, partner_id))

            if asset and amount > 0:
                liquidity = await RiskEngineV1.evaluate_liquidity_risk(
                    actor_id,
                    asset,
                    amount,
                    deal_id=deal_id,
                    _session=session,
                    _inline=True,
                )
                checks.append(liquidity)

            checks.append(
                await RiskEngineV1._check_concentration(
                    session,
                    partner_id=partner_id,
                    asset=asset,
                    amount=amount,
                )
            )

        return await RiskEngineV1._finalize_evaluation(
            actor_id,
            evaluation_type=RiskEvaluationType.DEAL.value,
            checks=checks,
            deal_id=deal_id,
            partner_id=partner_id,
            asset=asset,
            amount=amount,
        )

    @staticmethod
    async def evaluate_partner_risk(
        actor_id: int,
        partner_id: uuid.UUID,
        *,
        amount: Decimal | None = None,
    ) -> dict[str, Any]:
        if not await RiskEngineV1.user_can_read(actor_id):
            raise RiskEngineError("Access denied")

        async with get_session() as session:
            partner = await PartnerRepository(session).get_by_id(partner_id)
            if partner is None:
                raise RiskEngineError(f"Partner not found: {partner_id}")

            resolved_amount = amount or Decimal("0")
            checks: list[dict[str, Any]] = []
            checks.extend(await RiskEngineV1._check_partner_profile(session, partner_id))
            if resolved_amount > 0:
                checks.append(
                    await RiskEngineV1._check_partner_limits(
                        session, partner_id, resolved_amount
                    )
                )
                checks.append(
                    await RiskEngineV1._check_kyc(session, partner_id, resolved_amount)
                )
            else:
                checks.append(await RiskEngineV1._check_kyc(session, partner_id, Decimal("1")))
            checks.append(await RiskEngineV1._check_country(session, partner_id))
            checks.append(await RiskEngineV1._check_sanctions(session, partner_id))

        return await RiskEngineV1._finalize_evaluation(
            actor_id,
            evaluation_type=RiskEvaluationType.PARTNER.value,
            checks=checks,
            partner_id=partner_id,
            amount=resolved_amount if resolved_amount > 0 else None,
        )

    @staticmethod
    async def evaluate_liquidity_risk(
        actor_id: int,
        asset: str,
        amount: Decimal,
        *,
        deal_id: uuid.UUID | None = None,
        location: str | None = None,
        _session=None,
        _inline: bool = False,
    ) -> dict[str, Any]:
        if not _inline and not await RiskEngineV1.user_can_read(actor_id):
            raise RiskEngineError("Access denied")

        from services.pg_liquidity_engine import LiquidityEngineV1

        check = await LiquidityEngineV1.check_liquidity(
            asset,
            amount,
            location=location,
            deal_id=deal_id,
        )

        result = {
            "check_type": "liquidity_sufficiency",
            "rule_type": RiskRuleType.LIQUIDITY_RISK.value,
            "passed": check["sufficient"],
            "risk_level": RiskLevel.LOW.value if check["sufficient"] else RiskLevel.HIGH.value,
            "message": (
                f"Liquidity sufficient: {check['total_free']} free for {amount} {asset}"
                if check["sufficient"]
                else (
                    f"Insufficient liquidity: need {amount} {asset}, "
                    f"free {check['total_free']}"
                )
            ),
            "asset": asset,
            "amount": str(amount),
            "total_free": str(check["total_free"]),
            "operation_type": "DEAL",
        }
        if not check["sufficient"]:
            result["decision_hint"] = RiskDecisionResult.REVIEW_REQUIRED.value

        if _inline:
            return result

        return await RiskEngineV1._finalize_evaluation(
            actor_id,
            evaluation_type=RiskEvaluationType.LIQUIDITY.value,
            checks=[result],
            deal_id=deal_id,
            asset=asset,
            amount=amount,
        )

    @staticmethod
    async def approve_override(
        actor_id: int,
        decision_id: uuid.UUID,
        *,
        reason: str,
    ) -> dict[str, Any]:
        if actor_id != OWNER_ID:
            raise RiskEngineError("Owner approval required for risk override")

        async with get_session() as session:
            decision = await RiskDecisionRepository(session).get_by_id(decision_id)
            if decision is None:
                raise RiskEngineError(f"Decision not found: {decision_id}")
            if decision.decision == RiskDecisionResult.APPROVED.value and decision.override_by:
                raise RiskEngineError("Decision already overridden")

            old_decision = decision.decision
            decision = await RiskDecisionRepository(session).apply_override(
                decision_id,
                override_by=actor_id,
                override_reason=reason,
            )
            resolved = await BlockedOperationRepository(session).resolve_for_decision(
                decision_id
            )

            await RiskEngineV1._audit(
                session,
                user_id=actor_id,
                action=AuditAction.RISK_OVERRIDE.value,
                entity_id=str(decision_id),
                old_value={"decision": old_decision},
                new_value={"decision": RiskDecisionResult.APPROVED.value, "reason": reason},
            )

        aggregate_id = decision.deal_id or decision.partner_id or decision_id
        await RiskEngineV1._publish_event(
            "risk.override",
            aggregate_id,
            {"decision_id": str(decision_id), "reason": reason, "resolved_blocks": resolved},
        )
        await RiskEngineV1._publish_event(
            "risk.approved",
            aggregate_id,
            {"decision_id": str(decision_id), "via": "override"},
        )

        return {
            "decision_id": str(decision_id),
            "decision": RiskDecisionResult.APPROVED.value,
            "override_by": actor_id,
            "override_reason": reason,
            "resolved_blocks": resolved,
        }
