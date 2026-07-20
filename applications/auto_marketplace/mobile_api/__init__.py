__all__ = ["PortalEngine", "portal_engine"]


def __getattr__(name: str):
    if name in ("PortalEngine", "portal_engine"):
        from applications.auto_marketplace.mobile_api.engine import PortalEngine, portal_engine

        return PortalEngine if name == "PortalEngine" else portal_engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
