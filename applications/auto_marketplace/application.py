# AutoMarketplaceApplication — application facade.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.analytics.service import AnalyticsService, analytics_service
from applications.auto_marketplace.catalog.service import CatalogService, catalog_service
from applications.auto_marketplace.config import DEFAULT_CONFIG, AutoMarketplaceConfig
from applications.auto_marketplace.crm.service import CRMService, crm_service
from applications.auto_marketplace.customers.service import CustomerService, customer_service
from applications.auto_marketplace.dealers.service import DealerService, dealer_service
from applications.auto_marketplace.delivery.service import DeliveryService, delivery_service
from applications.auto_marketplace.documents.service import DocumentService, document_service
from applications.auto_marketplace.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.auto_marketplace.inventory.service import InventoryService, inventory_service
from applications.auto_marketplace.notifications.service import NotificationService, notification_service
from applications.auto_marketplace.payments.service import PaymentService, payment_service
from applications.auto_marketplace.pricing.service import (
    PricingService,
    RecommendationService,
    pricing_service,
    recommendation_service,
)
from applications.auto_marketplace.search.service import SearchService, search_service
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class AutoMarketplaceApplication:
    """Enterprise Auto Marketplace — consumes Platform Core v3.0 via bridges."""

    def __init__(
        self,
        *,
        config: AutoMarketplaceConfig | None = None,
        store: MarketplaceStore | None = None,
        catalog: CatalogService | None = None,
        dealers: DealerService | None = None,
        customers: CustomerService | None = None,
        crm: CRMService | None = None,
        inventory: InventoryService | None = None,
        pricing: PricingService | None = None,
        recommendations: RecommendationService | None = None,
        search: SearchService | None = None,
        documents: DocumentService | None = None,
        payments: PaymentService | None = None,
        delivery: DeliveryService | None = None,
        analytics: AnalyticsService | None = None,
        notifications: NotificationService | None = None,
        platform: PlatformBridge | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or marketplace_store
        self.catalog = catalog or catalog_service
        self.dealers = dealers or dealer_service
        self.customers = customers or customer_service
        self.crm = crm or crm_service
        self.inventory = inventory or inventory_service
        self.pricing = pricing or pricing_service
        self.recommendations = recommendations or recommendation_service
        self.search = search or search_service
        self.documents = documents or document_service
        self.payments = payments or payment_service
        self.delivery = delivery or delivery_service
        self.analytics = analytics or analytics_service
        self.notifications = notifications or notification_service
        self.platform = platform or platform_bridge

    def reset(self) -> None:
        self.store.reset()
        self.notifications.reset()

    def health(self) -> dict[str, Any]:
        return {
            "application": "auto_marketplace",
            "api_version": self.config.api_version,
            "metrics": self.analytics.dashboard_metrics(),
        }


auto_marketplace = AutoMarketplaceApplication()
