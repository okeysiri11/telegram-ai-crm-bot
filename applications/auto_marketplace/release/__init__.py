__all__ = ["ProductionEngine", "production_engine"]


def __getattr__(name: str):
    if name in ("ProductionEngine", "production_engine"):
        from applications.auto_marketplace.release.engine import ProductionEngine, production_engine

        return ProductionEngine if name == "ProductionEngine" else production_engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
