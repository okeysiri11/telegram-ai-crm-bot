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
    "payment.completed": {
        "aggregate_type": "payment",
        "description": "Payment completed",
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
    "settlement.created": {
        "aggregate_type": "settlement",
        "description": "Settlement created",
    },
    "settlement.started": {
        "aggregate_type": "settlement",
        "description": "Settlement started",
    },
    "settlement.completed": {
        "aggregate_type": "settlement",
        "description": "Settlement completed",
    },
    "settlement.failed": {
        "aggregate_type": "settlement",
        "description": "Settlement failed",
    },
    "risk.detected": {
        "aggregate_type": "risk",
        "description": "Risk condition detected",
    },
    "risk.review_required": {
        "aggregate_type": "risk",
        "description": "Risk review required",
    },
    "risk.approved": {
        "aggregate_type": "risk",
        "description": "Risk evaluation approved",
    },
    "risk.rejected": {
        "aggregate_type": "risk",
        "description": "Risk evaluation rejected",
    },
    "risk.override": {
        "aggregate_type": "risk",
        "description": "Risk decision manually overridden",
    },
    "market.quote.updated": {
        "aggregate_type": "market",
        "description": "Market quote updated",
    },
    "market.spread.changed": {
        "aggregate_type": "market",
        "description": "Market spread changed",
    },
    "market.source.failed": {
        "aggregate_type": "market",
        "description": "Market data source fetch failed",
    },
    "otc.order.created": {
        "aggregate_type": "otc",
        "description": "OTC order created",
    },
    "otc.quote.received": {
        "aggregate_type": "otc",
        "description": "OTC counterparty quote received",
    },
    "otc.match.created": {
        "aggregate_type": "otc",
        "description": "OTC match created",
    },
    "otc.order.filled": {
        "aggregate_type": "otc",
        "description": "OTC order fully filled",
    },
    "otc.execution.failed": {
        "aggregate_type": "otc",
        "description": "OTC execution leg failed",
    },
    "vehicle.cost.updated": {
        "aggregate_type": "vehicle",
        "description": "Vehicle total cost updated",
    },
    "vehicle.margin.updated": {
        "aggregate_type": "vehicle",
        "description": "Vehicle margin and target price updated",
    },
    "vehicle.import.started": {
        "aggregate_type": "vehicle",
        "description": "Vehicle marketplace import job started",
    },
    "vehicle.import.completed": {
        "aggregate_type": "vehicle",
        "description": "Vehicle marketplace import job completed",
    },
    "vehicle.imported": {
        "aggregate_type": "vehicle",
        "description": "Vehicle imported into inventory",
    },
    "vehicle.price.changed": {
        "aggregate_type": "vehicle",
        "description": "Vehicle price changed during marketplace import",
    },
    "vehicle.created": {
        "aggregate_type": "vehicle",
        "description": "Vehicle operation created",
    },
    "vehicle.arrived": {
        "aggregate_type": "vehicle",
        "description": "Vehicle arrived at warehouse",
    },
    "vehicle.listed": {
        "aggregate_type": "vehicle",
        "description": "Vehicle listed for sale",
    },
    "vehicle.reserved": {
        "aggregate_type": "vehicle",
        "description": "Vehicle reserved for sale",
    },
    "vehicle.sold": {
        "aggregate_type": "vehicle",
        "description": "Vehicle sold",
    },
    "vehicle.delivered": {
        "aggregate_type": "vehicle",
        "description": "Vehicle delivered to customer",
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
