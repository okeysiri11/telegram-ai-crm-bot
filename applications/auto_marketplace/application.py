# AutoMarketplaceApplication — application facade.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.ai.facade import AutoAIDomainEngine, auto_ai_domain_engine
from applications.auto_marketplace.ai_sales.engine import AISalesEngine, ai_sales_engine
from applications.auto_marketplace.analytics.service import AnalyticsService, analytics_service
from applications.auto_marketplace.business_intelligence.engine import BIEngine, bi_engine
from applications.auto_marketplace.buyers.engine import BuyersEngine, buyers_engine
from applications.auto_marketplace.catalog.service import CatalogService, catalog_service
from applications.auto_marketplace.config import DEFAULT_CONFIG, AutoMarketplaceConfig
from applications.auto_marketplace.crm.engine import CRMEngine, crm_engine
from applications.auto_marketplace.crm.service import CRMService, crm_service
from applications.auto_marketplace.customers.service import CustomerService, customer_service
from applications.auto_marketplace.dealers.service import DealerService, dealer_service
from applications.auto_marketplace.delivery.service import DeliveryService, delivery_service
from applications.auto_marketplace.documents.service import DocumentService, document_service
from applications.auto_marketplace.enterprise.facade import EnterpriseDomainEngine, enterprise_domain_engine
from applications.auto_marketplace.enterprise_automotive.facade import (
    EnterpriseAutomotiveSuite,
    enterprise_automotive,
)
from applications.auto_marketplace.vin_intelligence.facade import VINIntelligenceSuite, vin_intelligence
from applications.auto_marketplace.inspection_ai.facade import InspectionAISuite, inspection_ai
from applications.auto_marketplace.dealer_crm.facade import DealerCRMSuite, dealer_crm
from applications.auto_marketplace.favorites.service import FavoritesService, favorites_service
from applications.auto_marketplace.finance.engine import FinanceEngine, finance_engine
from applications.auto_marketplace.filters.search_engine import SearchEngine, search_engine
from applications.auto_marketplace.fleet.facade import FleetDomainEngine, fleet_domain_engine
from applications.auto_marketplace.garage.service import GarageService, garage_service
from applications.auto_marketplace.inspection.engine import InspectionEngine, inspection_engine
from applications.auto_marketplace.integrations.ecosystem_bridge import EcosystemBridge, ecosystem_bridge
from applications.auto_marketplace.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.auto_marketplace.inventory.service import InventoryService, inventory_service
from applications.auto_marketplace.inventory_engine.service import InventoryEngine, inventory_engine
from applications.auto_marketplace.marketplace.facade import (
    MarketplaceDomainEngine,
    marketplace_domain_engine,
)
from applications.auto_marketplace.media.service import MediaService, media_service
from applications.auto_marketplace.mobile_api.engine import PortalEngine, portal_engine
from applications.auto_marketplace.notifications.service import NotificationService, notification_service
from applications.auto_marketplace.payments.service import PaymentService, payment_service
from applications.auto_marketplace.pricing.service import (
    PricingService,
    RecommendationService,
    pricing_service,
    recommendation_service,
)
from applications.auto_marketplace.release.engine import ProductionEngine, production_engine
from applications.auto_marketplace.search.service import SearchService, search_service
from applications.auto_marketplace.service_centers.facade import ServiceDomainEngine, service_domain_engine
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transactions.facade import (
    TransactionDomainEngine,
    transaction_domain_engine,
)
from applications.auto_marketplace.transport.facade import LogisticsDomainEngine, logistics_domain_engine
from applications.auto_marketplace.vehicle_catalog.service import VehicleCatalogService, vehicle_catalog_service
from applications.auto_marketplace.vehicles.engine import VehiclesEngine, vehicles_engine


class AutoMarketplaceApplication:
    """Auto Marketplace — Platform Core v3 + Ecosystem v1.5 via bridges only."""

    def __init__(
        self,
        *,
        config: AutoMarketplaceConfig | None = None,
        store: MarketplaceStore | None = None,
        catalog: CatalogService | None = None,
        vehicles: VehiclesEngine | None = None,
        dealers: DealerService | None = None,
        buyers: BuyersEngine | None = None,
        customers: CustomerService | None = None,
        crm: CRMService | None = None,
        inventory: InventoryService | None = None,
        pricing: PricingService | None = None,
        recommendations: RecommendationService | None = None,
        search: SearchService | None = None,
        documents: DocumentService | None = None,
        favorites: FavoritesService | None = None,
        garage: GarageService | None = None,
        inspection: InspectionEngine | None = None,
        marketplace_domain: MarketplaceDomainEngine | None = None,
        auto_ai: AutoAIDomainEngine | None = None,
        transactions: TransactionDomainEngine | None = None,
        service: ServiceDomainEngine | None = None,
        logistics: LogisticsDomainEngine | None = None,
        fleet_domain: FleetDomainEngine | None = None,
        enterprise: EnterpriseDomainEngine | None = None,
        payments: PaymentService | None = None,
        delivery: DeliveryService | None = None,
        analytics: AnalyticsService | None = None,
        notifications: NotificationService | None = None,
        platform: PlatformBridge | None = None,
        ecosystem: EcosystemBridge | None = None,
        vehicle_catalog: VehicleCatalogService | None = None,
        inventory_engine_svc: InventoryEngine | None = None,
        media: MediaService | None = None,
        search_engine_svc: SearchEngine | None = None,
        crm_engine_svc: CRMEngine | None = None,
        ai_sales_engine_svc: AISalesEngine | None = None,
        finance_engine_svc: FinanceEngine | None = None,
        bi_engine_svc: BIEngine | None = None,
        portal_engine_svc: PortalEngine | None = None,
        production_engine_svc: ProductionEngine | None = None,
        enterprise_automotive_svc: EnterpriseAutomotiveSuite | None = None,
        vin_intelligence_svc: VINIntelligenceSuite | None = None,
        inspection_ai_svc: InspectionAISuite | None = None,
        dealer_crm_svc: DealerCRMSuite | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or marketplace_store
        self.catalog = catalog or catalog_service
        self.vehicles = vehicles or vehicles_engine
        self.dealers = dealers or dealer_service
        self.buyers = buyers or buyers_engine
        self.customers = customers or customer_service
        self.crm = crm or crm_service
        self.inventory = inventory or inventory_service
        self.pricing = pricing or pricing_service
        self.recommendations = recommendations or recommendation_service
        self.search = search or search_service
        self.documents = documents or document_service
        self.favorites = favorites or favorites_service
        self.garage = garage or garage_service
        self.inspection = inspection or inspection_engine
        self.marketplace = marketplace_domain or marketplace_domain_engine
        self.auto_ai = auto_ai or auto_ai_domain_engine
        self.transactions = transactions or transaction_domain_engine
        self.service = service or service_domain_engine
        self.logistics = logistics or logistics_domain_engine
        self.fleet_ops = fleet_domain or fleet_domain_engine
        self.enterprise = enterprise or enterprise_domain_engine
        self.payments = payments or payment_service
        self.delivery = delivery or delivery_service
        self.analytics = analytics or analytics_service
        self.notifications = notifications or notification_service
        self.platform = platform or platform_bridge
        self.ecosystem = ecosystem or ecosystem_bridge
        self.vehicle_catalog = vehicle_catalog or vehicle_catalog_service
        self.inventory_engine = inventory_engine_svc or inventory_engine
        self.media = media or media_service
        self.search_engine = search_engine_svc or search_engine
        self.crm_engine = crm_engine_svc or crm_engine
        self.ai_sales_engine = ai_sales_engine_svc or ai_sales_engine
        self.finance_engine = finance_engine_svc or finance_engine
        self.bi_engine = bi_engine_svc or bi_engine
        self.portal_engine = portal_engine_svc or portal_engine
        self.production_engine = production_engine_svc or production_engine
        self.enterprise_automotive = enterprise_automotive_svc or enterprise_automotive
        self.vin_intelligence = vin_intelligence_svc or vin_intelligence
        self.inspection_ai = inspection_ai_svc or inspection_ai
        self.dealer_crm = dealer_crm_svc or dealer_crm

    def reset(self) -> None:
        self.store.reset()
        self.notifications.reset()
        self.production_engine.maintenance.disable()

    def health(self) -> dict[str, Any]:
        return {
            "application": "auto_marketplace",
            "application_name": self.config.application_name,
            "application_version": self.config.application_version,
            "release_status": self.config.release_status,
            "platform_dependency": self.config.platform_dependency,
            "ecosystem_dependency": self.config.ecosystem_dependency,
            "enterprise_foundation": self.config.enterprise_foundation,
            "enterprise_automotive_suite": self.config.enterprise_automotive_suite,
            "vin_intelligence": self.config.vin_intelligence,
            "inspection_ai": self.config.inspection_ai,
            "dealer_crm": self.config.dealer_crm,
            "auto_marketplace_ready": True,
            "auto_ai_ready": True,
            "dealer_platform_ready": True,
            "enterprise_automotive_suite_ready": True,
            "vin_intelligence_ready": True,
            "digital_passport_ready": True,
            "vehicle_history_ai_ready": True,
            "fraud_detection_ready": True,
            "inspection_ai_ready": True,
            "damage_detection_ready": True,
            "vehicle_health_ai_ready": True,
            "repair_estimation_ready": True,
            "dealer_crm_ready": True,
            "trade_in_ai_ready": True,
            "inventory_intelligence_ready": True,
            "sales_ai_ready": True,
            "maintenance_mode": self.production_engine.maintenance.enabled,
            "api_version": self.config.api_version,
            "catalog_engine": self.config.catalog_engine,
            "crm_foundation": self.config.crm_foundation,
            "vin_engine": self.config.vin_engine,
            "dealer_engine": self.config.dealer_engine,
            "auto_ai_engine": self.config.auto_ai_engine,
            "recommendation_engine": self.config.recommendation_engine,
            "transaction_engine": self.config.transaction_engine,
            "auction_engine": self.config.auction_engine,
            "finance_engine": self.config.finance_engine,
            "insurance_engine": self.config.insurance_engine,
            "service_engine": self.config.service_engine,
            "parts_engine": self.config.parts_engine,
            "maintenance_engine": self.config.maintenance_engine,
            "transport_engine": self.config.transport_engine,
            "tracking_engine": self.config.tracking_engine,
            "customs_engine": self.config.customs_engine,
            "fleet_engine": self.config.fleet_engine,
            "rental_engine": self.config.rental_engine,
            "operations_engine": self.config.operations_engine,
            "enterprise_engine": self.config.enterprise_engine,
            "global_network": self.config.global_network,
            "production_ready": self.config.production_ready,
            "metrics": self.analytics.dashboard_metrics(),
            "foundation": {
                "catalog": self.catalog.overview(),
                "vehicles": self.vehicles.metrics(),
                "buyers": self.buyers.metrics(),
                "crm": self.crm.metrics(),
                "inspection": self.inspection.metrics(),
            },
            "marketplace": self.marketplace.metrics(),
            "auto_ai": self.auto_ai.metrics(),
            "transactions": self.transactions.metrics(),
            "service": self.service.metrics(),
            "logistics": self.logistics.metrics(),
            "fleet_ops": self.fleet_ops.metrics(),
            "enterprise": self.enterprise.metrics(),
            "enterprise_automotive": self.enterprise_automotive.status(),
            "vin_intelligence": self.vin_intelligence.status(),
            "inspection_ai": self.inspection_ai.status(),
            "dealer_crm": self.dealer_crm.status(),
            "health_deep": self.enterprise.health.deep(),
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
            "portal_users": self.store.portal_users.count(),
            "platform": self.platform.platform_health(),
            "ecosystem": self.ecosystem.ecosystem_health(),
        }


auto_marketplace = AutoMarketplaceApplication()
