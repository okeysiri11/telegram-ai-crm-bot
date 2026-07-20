__all__ = ["BIEngine", "bi_engine"]


def __getattr__(name: str):
    if name in ("BIEngine", "bi_engine"):
        from applications.auto_marketplace.business_intelligence.engine import BIEngine, bi_engine

        return BIEngine if name == "BIEngine" else bi_engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
