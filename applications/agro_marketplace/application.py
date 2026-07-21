# AgroMarketplaceApplication — application facade.

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.ai.engine import AgroAIEngine, agro_ai_engine
from applications.agro_marketplace.analytics.service import AnalyticsService, analytics_service
from applications.agro_marketplace.buyers.service import BuyerService, buyer_service
from applications.agro_marketplace.catalog.service import CatalogService, catalog_service
from applications.agro_marketplace.certification.service import CertificationService, certification_service
from applications.agro_marketplace.config import DEFAULT_CONFIG, AgroMarketplaceConfig
from applications.agro_marketplace.containers.service import ContainersService, containers_service
from applications.agro_marketplace.contracts.service import ContractService, contract_service
from applications.agro_marketplace.crm.engine import CRMEngine, crm_engine
from applications.agro_marketplace.crm.service import CRMService, crm_service
from applications.agro_marketplace.dashboard.service import DashboardService, dashboard_service
from applications.agro_marketplace.documents.service import DocumentService, document_service
from applications.agro_marketplace.documents.trade_service import TradeDocumentsService, trade_documents_service
from applications.agro_marketplace.export.ai_integration import ExportAIIntegration, export_ai
from applications.agro_marketplace.export.engine import ExportEngine, export_engine
from applications.agro_marketplace.export.service import ExportService, export_service
from applications.agro_marketplace.exporters.service import ExporterService, exporter_service
from applications.agro_marketplace.farmers.service import FarmerService, farmer_service
from applications.agro_marketplace.finance.service import FreightFinanceService, freight_finance_service
from applications.agro_marketplace.harvest.service import HarvestService, harvest_service
from applications.agro_marketplace.incoterms.service import IncotermsService, incoterms_service
from applications.agro_marketplace.insurance.service import InsuranceService, insurance_service
from applications.agro_marketplace.integrations.ecosystem_bridge import EcosystemBridge, ecosystem_bridge
from applications.agro_marketplace.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.agro_marketplace.inventory.engine import InventoryEngine, inventory_engine
from applications.agro_marketplace.logistics.engine import LogisticsEngine, logistics_engine
from applications.agro_marketplace.logistics.service import LogisticsService, logistics_service
from applications.agro_marketplace.marketplace.ai_integration import TradingAIIntegration, trading_ai
from applications.agro_marketplace.marketplace.engine import MarketplaceEngine, marketplace_engine
from applications.agro_marketplace.marketplace.trading_engine import TradingEngine, trading_engine
from applications.agro_marketplace.negotiations.engine import NegotiationEngine, negotiation_engine
from applications.agro_marketplace.notifications.service import NotificationService, notification_service
from applications.agro_marketplace.offers.service import OfferService, offer_service
from applications.agro_marketplace.orders.marketplace_service import (
    MarketplaceOrderService,
    marketplace_order_service,
)
from applications.agro_marketplace.orders.service import OrderService, order_service
from applications.agro_marketplace.payments.service import PaymentService, payment_service
from applications.agro_marketplace.ports.service import PortsService, ports_service
from applications.agro_marketplace.pricing.service import PricingService, pricing_service
from applications.agro_marketplace.product_catalog.service import ProductCatalogService, product_catalog_service
from applications.agro_marketplace.products.service import ProductService, product_service
from applications.agro_marketplace.quality.service import QualityService, quality_service
from applications.agro_marketplace.search.engine import AgroSearchEngine, agro_search_engine
from applications.agro_marketplace.security.permissions import PermissionService, permission_service
from applications.agro_marketplace.shared.store import AgroStore, agro_store
from applications.agro_marketplace.shipping.service import ShippingService, shipping_service
from applications.agro_marketplace.storage.service import StorageService, storage_service
from applications.agro_marketplace.suppliers.service import SupplierService, supplier_service
from applications.agro_marketplace.tracking.service import TrackingService, tracking_service
from applications.agro_marketplace.warehouse.engine import WarehouseEngine, warehouse_engine
from applications.agro_marketplace.warehouse.service import WarehouseService, warehouse_service


class AgroMarketplaceApplication:
    """Agricultural marketplace — Platform Core v3.0 + Ecosystem v1.5 via bridges only."""

    def __init__(
        self,
        *,
        config: AgroMarketplaceConfig | None = None,
        store: AgroStore | None = None,
        farmers: FarmerService | None = None,
        buyers: BuyerService | None = None,
        suppliers: SupplierService | None = None,
        exporters: ExporterService | None = None,
        products: ProductService | None = None,
        catalog: CatalogService | None = None,
        product_catalog: ProductCatalogService | None = None,
        orders: OrderService | None = None,
        marketplace_orders: MarketplaceOrderService | None = None,
        warehouse: WarehouseService | None = None,
        warehouse_engine_svc: WarehouseEngine | None = None,
        inventory: InventoryEngine | None = None,
        storage: StorageService | None = None,
        harvest: HarvestService | None = None,
        quality: QualityService | None = None,
        certification: CertificationService | None = None,
        search: AgroSearchEngine | None = None,
        pricing: PricingService | None = None,
        logistics: LogisticsService | None = None,
        logistics_engine_svc: LogisticsEngine | None = None,
        export: ExportService | None = None,
        export_engine_svc: ExportEngine | None = None,
        analytics: AnalyticsService | None = None,
        notifications: NotificationService | None = None,
        crm: CRMService | None = None,
        crm_engine_svc: CRMEngine | None = None,
        marketplace: MarketplaceEngine | None = None,
        trading: TradingEngine | None = None,
        negotiations: NegotiationEngine | None = None,
        offers: OfferService | None = None,
        contracts: ContractService | None = None,
        documents: DocumentService | None = None,
        trade_documents: TradeDocumentsService | None = None,
        payments: PaymentService | None = None,
        dashboard: DashboardService | None = None,
        permissions: PermissionService | None = None,
        trading_ai_svc: TradingAIIntegration | None = None,
        agro_ai: AgroAIEngine | None = None,
        ports: PortsService | None = None,
        shipping: ShippingService | None = None,
        containers: ContainersService | None = None,
        tracking: TrackingService | None = None,
        insurance: InsuranceService | None = None,
        freight_finance: FreightFinanceService | None = None,
        incoterms: IncotermsService | None = None,
        export_ai_svc: ExportAIIntegration | None = None,
        platform: PlatformBridge | None = None,
        ecosystem: EcosystemBridge | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or agro_store
        self.farmers = farmers or farmer_service
        self.buyers = buyers or buyer_service
        self.suppliers = suppliers or supplier_service
        self.exporters = exporters or exporter_service
        self.products = products or product_service
        self.catalog = catalog or catalog_service
        self.product_catalog = product_catalog or product_catalog_service
        self.orders = orders or order_service
        self.marketplace_orders = marketplace_orders or marketplace_order_service
        self.warehouse = warehouse or warehouse_service
        self.warehouse_engine = warehouse_engine_svc or warehouse_engine
        self.inventory = inventory or inventory_engine
        self.storage = storage or storage_service
        self.harvest = harvest or harvest_service
        self.quality = quality or quality_service
        self.certification = certification or certification_service
        self.search = search or agro_search_engine
        self.pricing = pricing or pricing_service
        self.logistics = logistics or logistics_service
        self.logistics_engine = logistics_engine_svc or logistics_engine
        self.export = export or export_service
        self.export_engine = export_engine_svc or export_engine
        self.analytics = analytics or analytics_service
        self.notifications = notifications or notification_service
        self.crm = crm or crm_service
        self.crm_engine = crm_engine_svc or crm_engine
        self.marketplace = marketplace or marketplace_engine
        self.trading = trading or trading_engine
        self.negotiations = negotiations or negotiation_engine
        self.offers = offers or offer_service
        self.contracts = contracts or contract_service
        self.documents = documents or document_service
        self.trade_documents = trade_documents or trade_documents_service
        self.payments = payments or payment_service
        self.dashboard = dashboard or dashboard_service
        self.permissions = permissions or permission_service
        self.trading_ai = trading_ai_svc or trading_ai
        self.agro_ai = agro_ai or agro_ai_engine
        self.ports = ports or ports_service
        self.shipping = shipping or shipping_service
        self.containers = containers or containers_service
        self.tracking = tracking or tracking_service
        self.insurance = insurance or insurance_service
        self.freight_finance = freight_finance or freight_finance_service
        self.incoterms = incoterms or incoterms_service
        self.export_ai = export_ai_svc or export_ai
        self.platform = platform or platform_bridge
        self.ecosystem = ecosystem or ecosystem_bridge

    def reset(self) -> None:
        self.store.reset()
        self.notifications.reset()
        self.agro_ai.agents.registry._seeded = False
        self.agro_ai.knowledge._seeded = False
        self.ports._seeded = False
        self.trade_documents._seeded = False

    def health(self) -> dict[str, Any]:
        return {
            "application": "agro_marketplace",
            "application_name": self.config.application_name,
            "application_version": self.config.application_version,
            "platform_dependency": self.config.platform_dependency,
            "ecosystem_dependency": self.config.ecosystem_dependency,
            "api_version": self.config.api_version,
            "catalog_layer": self.config.catalog_layer,
            "warehouse_layer": self.config.warehouse_layer,
            "inventory_layer": self.config.inventory_layer,
            "harvest_layer": self.config.harvest_layer,
            "crm_layer": self.config.crm_layer,
            "marketplace_layer": self.config.marketplace_layer,
            "trading_layer": self.config.trading_layer,
            "negotiation_layer": self.config.negotiation_layer,
            "agro_ai": self.config.agro_ai,
            "export_engine": self.config.export_engine,
            "metrics": self.analytics.dashboard_metrics(),
            "ai": self.agro_ai.metrics(),
            "crm": self.crm_engine.metrics(),
            "marketplace": self.marketplace.metrics(),
            "export": self.export_engine.metrics(),
            "logistics": self.logistics_engine.metrics(),
            "catalog_products": self.store.agro_products.count(),
            "agro_warehouses": self.store.agro_warehouses.count(),
            "inventory_items": self.store.inventory_items.count(),
            "harvest_records": self.store.harvest_records.count(),
            "platform": self.platform.platform_health(),
            "ecosystem": self.ecosystem.ecosystem_health(),
        }


agro_marketplace = AgroMarketplaceApplication()
