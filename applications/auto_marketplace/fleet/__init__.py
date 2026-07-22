"""Fleet domain — Sprint 10.7."""

from __future__ import annotations

from typing import Any

__all__ = ["FleetDomainEngine", "fleet_domain_engine", "FleetEngine", "fleet_engine"]


def __getattr__(name: str) -> Any:
    if name in {"FleetDomainEngine", "fleet_domain_engine"}:
        from applications.auto_marketplace.fleet.facade import FleetDomainEngine, fleet_domain_engine

        return FleetDomainEngine if name == "FleetDomainEngine" else fleet_domain_engine
    if name in {"FleetEngine", "fleet_engine"}:
        from applications.auto_marketplace.fleet.engine import FleetEngine, fleet_engine

        return FleetEngine if name == "FleetEngine" else fleet_engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
