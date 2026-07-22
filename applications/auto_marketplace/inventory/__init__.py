from applications.auto_marketplace.inventory.service import InventoryService, inventory_service

__all__ = [
    "InventoryService",
    "inventory_service",
    "PartsInventoryEngine",
    "parts_inventory_engine",
]


def __getattr__(name: str):
    if name in {"PartsInventoryEngine", "parts_inventory_engine"}:
        from applications.auto_marketplace.inventory.parts_engine import (
            PartsInventoryEngine,
            parts_inventory_engine,
        )

        return PartsInventoryEngine if name == "PartsInventoryEngine" else parts_inventory_engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
