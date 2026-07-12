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
