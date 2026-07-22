from applications.auto_marketplace.leasing.engine import LeasingEngine, leasing_engine

__all__ = [
    "LeasingEngine",
    "leasing_engine",
    "FleetLeasingEngine",
    "fleet_leasing_engine",
]


def __getattr__(name: str):
    if name in {"FleetLeasingEngine", "fleet_leasing_engine"}:
        from applications.auto_marketplace.leasing.fleet_engine import FleetLeasingEngine, fleet_leasing_engine

        return FleetLeasingEngine if name == "FleetLeasingEngine" else fleet_leasing_engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
