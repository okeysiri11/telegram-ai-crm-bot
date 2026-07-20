# Finance package — import engine from finance.engine directly to avoid circular imports.

__all__ = ["FinanceEngine", "finance_engine"]


def __getattr__(name: str):
    if name in ("FinanceEngine", "finance_engine"):
        from applications.auto_marketplace.finance.engine import FinanceEngine, finance_engine

        return FinanceEngine if name == "FinanceEngine" else finance_engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
