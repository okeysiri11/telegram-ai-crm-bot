from applications.auto_marketplace.dispatch.engine import DispatchEngine, dispatch_engine

__all__ = [
    "DispatchEngine",
    "dispatch_engine",
    "FleetDispatchEngine",
    "fleet_dispatch_engine",
]


def __getattr__(name: str):
    if name in {"FleetDispatchEngine", "fleet_dispatch_engine"}:
        from applications.auto_marketplace.dispatch.fleet_engine import FleetDispatchEngine, fleet_dispatch_engine

        return FleetDispatchEngine if name == "FleetDispatchEngine" else fleet_dispatch_engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
