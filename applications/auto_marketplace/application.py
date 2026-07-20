# AutoMarketplaceApplication — application facade.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.ai_sales.engine import AISalesEngine, ai_sales_engine
from applications.auto_marketplace.analytics.service import AnalyticsService, analytics_service
from applications.auto_marketplace.business_intelligence.engine import BIEngine, bi_engine
from applications.auto_marketplace.catalog.service import CatalogService, catalog_service
from applications.auto_marketplace.config import DEFAULT_CONFIG, AutoMarketplaceConfig
from applications.auto_marketplace.crm.engine import CRMEngine, crm_engine
from applications.auto_marketplace.crm.service import CRMService, crm_service
from applications.auto_marketplace.customers.service import CustomerService, customer_service
from applications.auto_marketplace.dealers.service import DealerService, dealer_service
from applications.auto_marketplace.delivery.service import DeliveryService, delivery_service
from applications.auto_marketplace.documents.service import DocumentService, document_service
from applications.auto_marketplace.finance.engine import FinanceEngine, finance_engine
from applications.auto_marketplace.filters.search_engine import SearchEngine, search_engine
from applications.auto_marketplace.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.auto_marketplace.inventory.service import InventoryService, inventory_service
from applications.auto_marketplace.inventory_engine.service import InventoryEngine, inventory_engine
from applications.auto_marketplace.media.service import MediaService, media_service
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
from applications.auto_marketplace.vehicle_catalog.service import VehicleCatalogService, vehicle_catalog_service


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
        vehicle_catalog: VehicleCatalogService | None = None,
        inventory_engine_svc: InventoryEngine | None = None,
        media: MediaService | None = None,
        search_engine_svc: SearchEngine | None = None,
        crm_engine_svc: CRMEngine | None = None,
        ai_sales_engine_svc: AISalesEngine | None = None,
        finance_engine_svc: FinanceEngine | None = None,
        bi_engine_svc: BIEngine | None = None,
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
        self.vehicle_catalog = vehicle_catalog or vehicle_catalog_service
        self.inventory_engine = inventory_engine_svc or inventory_engine
        self.media = media or media_service
        self.search_engine = search_engine_svc or search_engine
        self.crm_engine = crm_engine_svc or crm_engine
        self.ai_sales_engine = ai_sales_engine_svc or ai_sales_engine
        self.finance_engine = finance_engine_svc or finance_engine
        self.bi_engine = bi_engine_svc or bi_engine

    def reset(self) -> None:
        self.store.reset()
        self.notifications.reset()

    def health(self) -> dict[str, Any]:
        return {
            "application": "auto_marketplace",
            "application_version": self.config.application_version,
            "api_version": self.config.api_version,
            "metrics": self.analytics.dashboard_metrics(),
            "catalog_vehicles": self.store.catalog_vehicles.count(),
            "crm_leads": self.store.crm_leads.count(),
            "crm_deals": self.store.crm_deals.count(),
            "ai_conversations": self.store.conversation_sessions.count(),
            "ai_offers": self.store.ai_offers.count(),
            "finance_documents": self.store.finance_documents.count(),
            "contracts": self.store.contracts.count(),
            "finance_payments": self.store.finance_payments.count(),
            "bi_dashboards": self.store.bi_dashboards.count(),
            "bi_reports": self.store.bi_reports.count(),
        }


auto_marketplace = AutoMarketplaceApplication()
