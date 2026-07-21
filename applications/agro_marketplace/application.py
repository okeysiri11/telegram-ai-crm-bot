# AgroMarketplaceApplication — application facade.

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.analytics.service import AnalyticsService, analytics_service
from applications.agro_marketplace.buyers.service import BuyerService, buyer_service
from applications.agro_marketplace.catalog.service import CatalogService, catalog_service
from applications.agro_marketplace.certification.service import CertificationService, certification_service
from applications.agro_marketplace.config import DEFAULT_CONFIG, AgroMarketplaceConfig
from applications.agro_marketplace.crm.service import CRMService, crm_service
from applications.agro_marketplace.dashboard.service import DashboardService, dashboard_service
from applications.agro_marketplace.documents.service import DocumentService, document_service
from applications.agro_marketplace.export.service import ExportService, export_service
from applications.agro_marketplace.farmers.service import FarmerService, farmer_service
from applications.agro_marketplace.harvest.service import HarvestService, harvest_service
from applications.agro_marketplace.integrations.ecosystem_bridge import EcosystemBridge, ecosystem_bridge
from applications.agro_marketplace.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.agro_marketplace.inventory.engine import InventoryEngine, inventory_engine
from applications.agro_marketplace.logistics.service import LogisticsService, logistics_service
from applications.agro_marketplace.notifications.service import NotificationService, notification_service
from applications.agro_marketplace.orders.service import OrderService, order_service
from applications.agro_marketplace.payments.service import PaymentService, payment_service
from applications.agro_marketplace.pricing.service import PricingService, pricing_service
from applications.agro_marketplace.product_catalog.service import ProductCatalogService, product_catalog_service
from applications.agro_marketplace.products.service import ProductService, product_service
from applications.agro_marketplace.quality.service import QualityService, quality_service
from applications.agro_marketplace.search.engine import AgroSearchEngine, agro_search_engine
from applications.agro_marketplace.security.permissions import PermissionService, permission_service
from applications.agro_marketplace.shared.store import AgroStore, agro_store
from applications.agro_marketplace.storage.service import StorageService, storage_service
from applications.agro_marketplace.suppliers.service import SupplierService, supplier_service
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
        products: ProductService | None = None,
        catalog: CatalogService | None = None,
        product_catalog: ProductCatalogService | None = None,
        orders: OrderService | None = None,
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
        export: ExportService | None = None,
        analytics: AnalyticsService | None = None,
        notifications: NotificationService | None = None,
        crm: CRMService | None = None,
        documents: DocumentService | None = None,
        payments: PaymentService | None = None,
        dashboard: DashboardService | None = None,
        permissions: PermissionService | None = None,
        platform: PlatformBridge | None = None,
        ecosystem: EcosystemBridge | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or agro_store
        self.farmers = farmers or farmer_service
        self.buyers = buyers or buyer_service
        self.suppliers = suppliers or supplier_service
        self.products = products or product_service
        self.catalog = catalog or catalog_service
        self.product_catalog = product_catalog or product_catalog_service
        self.orders = orders or order_service
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
        self.export = export or export_service
        self.analytics = analytics or analytics_service
        self.notifications = notifications or notification_service
        self.crm = crm or crm_service
        self.documents = documents or document_service
        self.payments = payments or payment_service
        self.dashboard = dashboard or dashboard_service
        self.permissions = permissions or permission_service
        self.platform = platform or platform_bridge
        self.ecosystem = ecosystem or ecosystem_bridge

    def reset(self) -> None:
        self.store.reset()
        self.notifications.reset()

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
            "metrics": self.analytics.dashboard_metrics(),
            "catalog_products": self.store.agro_products.count(),
            "agro_warehouses": self.store.agro_warehouses.count(),
            "inventory_items": self.store.inventory_items.count(),
            "harvest_records": self.store.harvest_records.count(),
            "platform": self.platform.platform_health(),
            "ecosystem": self.ecosystem.ecosystem_health(),
        }


agro_marketplace = AgroMarketplaceApplication()
