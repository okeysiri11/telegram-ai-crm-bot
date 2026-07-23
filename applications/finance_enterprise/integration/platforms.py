"""Platform financial adapters — automotive, agro, port, crypto, legal (declarative)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.integration.event_bus import FinancialEventBus
from applications.finance_enterprise.shared.exceptions import ValidationError
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PlatformIntegration:
    """Generic cross-platform financial integration (does not modify source platforms)."""

    def __init__(
        self,
        *,
        platform: str,
        operation_types: list[str],
        store: FinanceEnterpriseStore | None = None,
        bus: FinancialEventBus | None = None,
    ) -> None:
        self.store = store or finance_enterprise_store
        self.bus = bus or FinancialEventBus(self.store)
        self.platform = platform
        self.operation_types = list(operation_types)

    def operate(
        self,
        *,
        operation: str,
        amount: float = 0.0,
        reference: str = "",
        detail: str = "",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        op = operation.lower().strip()
        if op not in self.operation_types:
            raise ValidationError(f"operation must be one of {self.operation_types}")
        amt = float(amount)
        if amt < 0:
            raise ValidationError("amount must be non-negative")
        event = self.bus.publish(
            platform=self.platform,
            event_kind="settlement" if "settlement" in op else "transaction",
            payload={"operation": op, **(payload or {})},
            amount=amt,
            reference=reference or op,
        )
        oid = _id(f"int_{self.platform[:3]}")
        return self.store.int_operations.save(
            oid,
            {
                "operation_id": oid,
                "platform": self.platform,
                "operation": op,
                "amount": amt,
                "reference": reference,
                "detail": detail or f"{self.platform} {op}",
                "event_id": event["event_id"],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        ops = [o for o in self.store.int_operations.list_all() if o["platform"] == self.platform]
        return {
            "platform": self.platform,
            "operations": len(ops),
            "types": self.operation_types,
        }


def automotive_integration(store=None, bus=None) -> PlatformIntegration:
    return PlatformIntegration(
        platform="automotive",
        operation_types=list(DEFAULT_CONFIG.int_automotive_ops),
        store=store,
        bus=bus,
    )


def agro_integration(store=None, bus=None) -> PlatformIntegration:
    return PlatformIntegration(
        platform="agro",
        operation_types=list(DEFAULT_CONFIG.int_agro_ops),
        store=store,
        bus=bus,
    )


def port_integration(store=None, bus=None) -> PlatformIntegration:
    return PlatformIntegration(
        platform="port",
        operation_types=list(DEFAULT_CONFIG.int_port_ops),
        store=store,
        bus=bus,
    )


def crypto_integration(store=None, bus=None) -> PlatformIntegration:
    return PlatformIntegration(
        platform="crypto",
        operation_types=list(DEFAULT_CONFIG.int_crypto_ops),
        store=store,
        bus=bus,
    )


def legal_integration(store=None, bus=None) -> PlatformIntegration:
    return PlatformIntegration(
        platform="legal",
        operation_types=list(DEFAULT_CONFIG.int_legal_ops),
        store=store,
        bus=bus,
    )
