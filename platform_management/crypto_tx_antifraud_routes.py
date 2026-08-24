# Crypto/OTC payout — management HTTP API — Sprint 48.0/48.1.
# SECURITY-CRITICAL. Moved here from services/crypto_tx_antifraud_router.py
# in Sprint 48.1 to fix a layering violation flagged during the Sprint 48.0
# audit: services/ is business logic with no direct HTTP exposure per
# CLAUDE.md; HTTP surface belongs in platform_management/ (or routers/).
#
# Every handler here delegates to services.crypto_payout_orchestrator
# .CryptoPayoutOrchestrator — the SAME canonical service the Telegram bot
# calls (routers/crypto_tx_antifraud_router.py). This module contains no
# duplicate-detection or state-transition logic of its own; it only
# translates HTTP <-> the orchestrator's calls/results.
#
# The old generic `POST /crypto-tx/register` endpoint (Sprint 48.0) is
# intentionally NOT carried over here: it let a caller register/claim a
# tx_hash without going through deal validation, i.e. a direct-API bypass
# of the orchestrator. Payout confirmation must go through
# `POST /crypto-tx/deals/{deal_id}/confirm-payout` instead.

from __future__ import annotations

import logging
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any

from aiohttp import web

from platform_management.permissions import ManagementRole, require_role
from services.crypto_payout_orchestrator import (
    CryptoAntifraudError,
    CryptoDealInvalidStateError,
    CryptoDealNotFoundError,
    CryptoPayoutOrchestrator,
    CryptoPayoutResultStatus,
    CryptoTxOverrideDeniedError,
    CryptoTxOverrideUnavailableError,
)

logger = logging.getLogger(__name__)


def _ok(data: Any, *, status: int = 200) -> web.Response:
    return web.json_response({"success": True, "data": data}, status=status)


def _err(msg: str, *, status: int = 400) -> web.Response:
    return web.json_response({"success": False, "error": msg}, status=status)


def _actor_id(ctx: Any, body: dict[str, Any]) -> int:
    return int(getattr(ctx, "actor_telegram_id", None) or body.get("actor_id") or 0)


def _role_for(ctx: Any) -> str:
    """Maps the web-authenticated ManagementRole to the same role vocabulary
    the orchestrator/engine use for the Telegram bot's authenticated_role
    (services/vertical_role_registry.py). OWNER is the only web-side role
    that maps into PRIVILEGED_OVERRIDE_ROLES — READ_ONLY/ADMINISTRATOR are
    treated as a regular operator/cashier for this endpoint's purposes."""
    role = str(getattr(ctx, "role", None) or "")
    return "owner" if role == ManagementRole.OWNER.value else "operator"


def _tx_dict(tx) -> dict[str, Any] | None:
    if tx is None:
        return None
    return {
        "id": str(tx.id),
        "network": tx.network,
        "tx_hash": tx.tx_hash,
        "token": tx.token,
        "log_index": tx.log_index,
        "wallet_address": tx.wallet_address,
        "amount": str(tx.amount),
        "deal_id": str(tx.deal_id) if tx.deal_id else None,
        "payout_id": str(tx.payout_id) if tx.payout_id else None,
        "legacy_deal_id": tx.legacy_deal_id,
        "legacy_payment_id": tx.legacy_payment_id,
        "customer_id": tx.customer_id,
        "status": tx.status,
        "first_seen_at": tx.first_seen_at.isoformat() if tx.first_seen_at else None,
        "registered_by": tx.registered_by,
        "approved_by": tx.approved_by,
    }


def _warning_dict(warning) -> dict[str, Any] | None:
    if warning is None:
        return None
    return {
        "tx_hash": warning.tx_hash,
        "network": warning.network,
        "token": warning.token,
        "amount": str(warning.amount),
        "wallet_address": warning.wallet_address,
        "previous_deal_id": warning.previous_deal_id,
        "previous_payout_id": warning.previous_payout_id,
        "previous_legacy_deal_id": warning.previous_legacy_deal_id,
        "previous_legacy_payment_id": warning.previous_legacy_payment_id,
        "previous_customer_id": warning.previous_customer_id,
        "previous_operator_id": warning.previous_operator_id,
        "previous_status": warning.previous_status,
        "first_seen_at": warning.first_seen_at.isoformat() if warning.first_seen_at else None,
        "anomalies": list(warning.anomalies),
    }


@require_role(ManagementRole.ADMINISTRATOR)
async def get_deal_summary(request: web.Request, ctx=None) -> web.Response:
    try:
        deal_id = int(request.match_info["deal_id"])
    except (KeyError, ValueError):
        return _err("deal_id must be an integer")
    try:
        summary = await CryptoPayoutOrchestrator.get_deal_summary(deal_id)
    except CryptoDealNotFoundError:
        return _err(f"deal {deal_id} not found", status=404)
    return _ok(summary)


@require_role(ManagementRole.ADMINISTRATOR)
async def confirm_payout(request: web.Request, ctx=None) -> web.Response:
    try:
        deal_id = int(request.match_info["deal_id"])
    except (KeyError, ValueError):
        return _err("deal_id must be an integer")
    try:
        body = await request.json()
    except Exception:
        body = {}
    try:
        amount = Decimal(str(body.get("amount")))
    except (InvalidOperation, TypeError):
        return _err("amount is required and must be numeric")
    for field in ("network", "tx_hash", "token", "wallet_address"):
        if not body.get(field):
            return _err(f"{field} is required")

    actor_id = _actor_id(ctx, body)
    try:
        result = await CryptoPayoutOrchestrator.confirm_payout(
            deal_id=deal_id,
            network=str(body["network"]),
            tx_hash=str(body["tx_hash"]),
            token=str(body["token"]),
            amount=amount,
            wallet_address=str(body["wallet_address"]),
            actor_id=actor_id,
            actor_role=_role_for(ctx),
            log_index=str(body.get("log_index") or "0"),
        )
    except CryptoDealNotFoundError:
        return _err(f"deal {deal_id} not found", status=404)
    except CryptoDealInvalidStateError as exc:
        return _err(str(exc), status=409)
    except CryptoAntifraudError as exc:
        return _err(str(exc), status=409)

    status_code = 200 if result.status != CryptoPayoutResultStatus.DUPLICATE else 409
    return _ok(
        {
            "status": result.status.value,
            "transaction": _tx_dict(result.transaction),
            "warning": _warning_dict(result.warning),
            "deal_id": result.deal_id,
            "payment_id": result.payment_id,
        },
        status=status_code,
    )


@require_role(ManagementRole.ADMINISTRATOR)
async def cancel_tx(request: web.Request, ctx=None) -> web.Response:
    tx_id = uuid.UUID(request.match_info["tx_id"])
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not body.get("reason"):
        return _err("reason is required to cancel")
    try:
        tx = await CryptoPayoutOrchestrator.cancel(
            tx_id, actor_id=_actor_id(ctx, body), reason=str(body["reason"])
        )
    except CryptoAntifraudError as exc:
        return _err(str(exc), status=409)
    return _ok({"transaction": _tx_dict(tx)})


@require_role(ManagementRole.ADMINISTRATOR)
async def request_review(request: web.Request, ctx=None) -> web.Response:
    tx_id = uuid.UUID(request.match_info["tx_id"])
    try:
        body = await request.json()
    except Exception:
        body = {}
    try:
        tx = await CryptoPayoutOrchestrator.request_review(
            tx_id, actor_id=_actor_id(ctx, body), reason=body.get("reason")
        )
    except CryptoAntifraudError as exc:
        return _err(str(exc), status=409)
    return _ok({"transaction": _tx_dict(tx)})


@require_role(ManagementRole.OWNER)
async def approve_override(request: web.Request, ctx=None) -> web.Response:
    """Requirement 6/10: only ManagementRole.OWNER reaches this handler at
    all — the orchestrator/engine's own PRIVILEGED_OVERRIDE_ROLES check runs
    again as defense in depth. Sprint 48.1: always ends in 503 today — see
    CryptoTxOverrideUnavailableError — because no real step-up
    authentication provider exists yet; a client-supplied field can never
    substitute for one."""
    tx_id = uuid.UUID(request.match_info["tx_id"])
    try:
        body = await request.json()
    except Exception:
        body = {}
    try:
        tx = await CryptoPayoutOrchestrator.approve_override(
            tx_id,
            approver_id=_actor_id(ctx, body),
            approver_role=_role_for(ctx),
            reason=str(body.get("reason") or ""),
            confirmed=bool(body.get("confirmed")),
            step_up_token=body.get("step_up_token"),
        )
    except CryptoTxOverrideUnavailableError as exc:
        return _err(str(exc), status=503)
    except CryptoTxOverrideDeniedError as exc:
        return _err(str(exc), status=403)
    except CryptoAntifraudError as exc:
        return _err(str(exc), status=409)
    return _ok({"transaction": _tx_dict(tx)})


@require_role(ManagementRole.ADMINISTRATOR)
async def reject_override(request: web.Request, ctx=None) -> web.Response:
    tx_id = uuid.UUID(request.match_info["tx_id"])
    try:
        body = await request.json()
    except Exception:
        body = {}
    await CryptoPayoutOrchestrator.reject_override(
        tx_id, actor_id=_actor_id(ctx, body), reason=body.get("reason")
    )
    return _ok({"rejected": True})


ROUTE_SPECS = [
    ("GET", "deals/{deal_id}", get_deal_summary),
    ("POST", "deals/{deal_id}/confirm-payout", confirm_payout),
    ("POST", "{tx_id}/cancel", cancel_tx),
    ("POST", "{tx_id}/review", request_review),
    ("POST", "{tx_id}/override/approve", approve_override),
    ("POST", "{tx_id}/override/reject", reject_override),
]


def register_crypto_tx_antifraud_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    register_dual_prefix_routes(
        app,
        route_specs=ROUTE_SPECS,  # type: ignore[arg-type]
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/crypto-tx",
        legacy_prefix="/management/crypto-tx",
    )
    logger.info("crypto_tx_antifraud_routes_registered")
