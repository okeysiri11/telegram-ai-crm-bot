# CRM Event Bus type registry.

from __future__ import annotations

EVENT_REGISTRY: dict[str, dict[str, str]] = {
    "deal.created": {
        "aggregate_type": "deal",
        "description": "Deal created",
    },
    "deal.updated": {
        "aggregate_type": "deal",
        "description": "Deal updated",
    },
    "deal.closed": {
        "aggregate_type": "deal",
        "description": "Deal closed",
    },
    "payment.received": {
        "aggregate_type": "payment",
        "description": "Payment received",
    },
    "payment.sent": {
        "aggregate_type": "payment",
        "description": "Payment sent",
    },
    "ledger.entry.created": {
        "aggregate_type": "ledger_entry",
        "description": "Ledger entry created",
    },
    "commission.accrued": {
        "aggregate_type": "commission",
        "description": "Commission accrued",
    },
    "partner.assigned": {
        "aggregate_type": "partner",
        "description": "Partner assigned",
    },
    "partner.unassigned": {
        "aggregate_type": "partner",
        "description": "Partner unassigned",
    },
    "partner.created": {
        "aggregate_type": "partner",
        "description": "Partner created",
    },
    "partner.updated": {
        "aggregate_type": "partner",
        "description": "Partner updated",
    },
    "partner.blocked": {
        "aggregate_type": "partner",
        "description": "Partner blocked",
    },
    "partner.limit_exceeded": {
        "aggregate_type": "partner",
        "description": "Partner limit exceeded",
    },
    "partner.kyc_approved": {
        "aggregate_type": "partner",
        "description": "Partner KYC approved",
    },
    "partner.kyc_rejected": {
        "aggregate_type": "partner",
        "description": "Partner KYC rejected",
    },
    "kyc.started": {
        "aggregate_type": "kyc",
        "description": "KYC process started",
    },
    "kyc.approved": {
        "aggregate_type": "kyc",
        "description": "KYC approved",
    },
    "kyc.rejected": {
        "aggregate_type": "kyc",
        "description": "KYC rejected",
    },
    "aml.review_required": {
        "aggregate_type": "aml",
        "description": "AML manual review required",
    },
    "price.updated": {
        "aggregate_type": "price",
        "description": "Market price updated",
    },
    "spread.changed": {
        "aggregate_type": "price",
        "description": "Spread rule changed",
    },
    "partner.price.updated": {
        "aggregate_type": "partner",
        "description": "Partner pricing updated",
    },
    "liquidity.reserved": {
        "aggregate_type": "liquidity",
        "description": "Liquidity reserved for deal",
    },
    "liquidity.released": {
        "aggregate_type": "liquidity",
        "description": "Liquidity reservation released",
    },
    "liquidity.shortage": {
        "aggregate_type": "liquidity",
        "description": "Liquidity shortage detected",
    },
    "liquidity.consumed": {
        "aggregate_type": "liquidity",
        "description": "Liquidity reservation consumed",
    },
    "user.created": {
        "aggregate_type": "user",
        "description": "User created",
    },
    "user.role_changed": {
        "aggregate_type": "user",
        "description": "User role changed",
    },
}

EVENT_TYPES: frozenset[str] = frozenset(EVENT_REGISTRY)


def validate_event_type(event_type: str) -> dict[str, str]:
    meta = EVENT_REGISTRY.get(event_type)
    if meta is None:
        raise ValueError(f"Unknown event type: {event_type}")
    return meta
