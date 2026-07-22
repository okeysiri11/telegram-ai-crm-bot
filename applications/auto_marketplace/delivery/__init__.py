from applications.auto_marketplace.delivery.service import DeliveryService, delivery_service

__all__ = [
    "DeliveryService",
    "delivery_service",
    "LogisticsDeliveryEngine",
    "logistics_delivery_engine",
]


def __getattr__(name: str):
    if name in {"LogisticsDeliveryEngine", "logistics_delivery_engine"}:
        from applications.auto_marketplace.delivery.logistics_engine import (
            LogisticsDeliveryEngine,
            logistics_delivery_engine,
        )

        return LogisticsDeliveryEngine if name == "LogisticsDeliveryEngine" else logistics_delivery_engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
