# ProductCatalogService — enterprise agricultural product catalog.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish

from applications.agro_marketplace.product_catalog.ai_integration import CatalogAIIntegration, catalog_ai
from applications.agro_marketplace.product_catalog.duplicate_detector import DuplicateDetector, duplicate_detector
from applications.agro_marketplace.product_catalog.events import CatalogProductCreatedEvent
from applications.agro_marketplace.product_catalog.models import (
    AgriculturalProduct,
    AvailabilityStatus,
    Crop,
    CropVariety,
    Packaging,
    UnitOfMeasure,
)
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.models import Product, ProductCategory, ProductStatus
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class ProductCatalogService:
    def __init__(
        self,
        store: AgroStore | None = None,
        duplicates: DuplicateDetector | None = None,
        ai: CatalogAIIntegration | None = None,
    ) -> None:
        self._store = store or agro_store
        self._duplicates = duplicates or duplicate_detector
        self._ai = ai or catalog_ai

    def _sync_legacy(self, product: AgriculturalProduct) -> None:
        status_map = {
            AvailabilityStatus.DRAFT: ProductStatus.DRAFT,
            AvailabilityStatus.AVAILABLE: ProductStatus.LISTED,
            AvailabilityStatus.RESERVED: ProductStatus.RESERVED,
            AvailabilityStatus.SOLD_OUT: ProductStatus.SOLD,
            AvailabilityStatus.ARCHIVED: ProductStatus.ARCHIVED,
            AvailabilityStatus.IN_TRANSIT: ProductStatus.LISTED,
        }
        legacy = Product(
            product_id=product.product_id,
            name=product.name,
            category_id=product.category_id,
            crop_id=product.crop_id,
            farmer_id=product.farmer_id,
            unit=product.uom.value,
            quantity=product.quantity,
            price=product.price,
            currency=product.currency,
            status=status_map.get(product.status, ProductStatus.DRAFT),
            metadata={
                "sku": product.sku,
                "region": product.region,
                "tags": list(product.tags),
                "attributes": dict(product.attributes),
            },
        )
        self._store.products.save(legacy.product_id, legacy)

    async def create(self, product: AgriculturalProduct) -> AgriculturalProduct:
        if not product.name:
            raise ValidationError("name is required")
        existing = self._store.agro_products.list_all()
        dupes = self._duplicates.find_duplicates(product, existing)
        if dupes:
            product.duplicate_of = dupes[0].product_id
        ai_dupes = await self._ai.detect_duplicates_ai(product, existing)
        if ai_dupes and not product.duplicate_of:
            product.duplicate_of = ai_dupes[0]
        category = await self._ai.auto_categorize(product)
        if not product.category_id:
            product.category_id = category
            product.tags = list({*product.tags, category})
        if not product.price:
            product.price = await self._ai.estimate_price(product)
        if not product.sku:
            product.sku = f"AGRO-{product.product_id[:8].upper()}"
        product.updated_at = time.time()
        saved = self._store.agro_products.save(product.product_id, product)
        self._sync_legacy(saved)
        await publish(
            CatalogProductCreatedEvent(
                product_id=saved.product_id,
                name=saved.name,
                sku=saved.sku,
                farmer_id=saved.farmer_id,
            )
        )
        return saved

    def get(self, product_id: str) -> AgriculturalProduct:
        product = self._store.agro_products.get(product_id)
        if product is None:
            raise NotFoundError("AgriculturalProduct", product_id)
        return product

    def list_products(
        self,
        *,
        status: AvailabilityStatus | None = None,
        include_archived: bool = False,
        category_id: str | None = None,
        farmer_id: str | None = None,
    ) -> list[AgriculturalProduct]:
        items = self._store.agro_products.list_all()
        if not include_archived:
            items = [p for p in items if p.status != AvailabilityStatus.ARCHIVED]
        if status:
            items = [p for p in items if p.status == status]
        if category_id:
            items = [p for p in items if p.category_id == category_id]
        if farmer_id:
            items = [p for p in items if p.farmer_id == farmer_id]
        return items

    async def update(self, product_id: str, **updates: Any) -> AgriculturalProduct:
        product = self.get(product_id)
        for key, value in updates.items():
            if hasattr(product, key) and value is not None:
                if key == "status" and isinstance(value, str):
                    value = AvailabilityStatus(value)
                if key == "uom" and isinstance(value, str):
                    value = UnitOfMeasure(value)
                setattr(product, key, value)
        product.updated_at = time.time()
        saved = self._store.agro_products.save(product_id, product)
        self._sync_legacy(saved)
        return saved

    async def bulk_import(self, products: list[AgriculturalProduct]) -> list[AgriculturalProduct]:
        return [await self.create(p) for p in products]

    async def bulk_update(self, updates: list[dict[str, Any]]) -> list[AgriculturalProduct]:
        results: list[AgriculturalProduct] = []
        for item in updates:
            product_id = item.get("product_id")
            if not product_id:
                raise ValidationError("product_id required for bulk update")
            payload = {k: v for k, v in item.items() if k != "product_id"}
            results.append(await self.update(product_id, **payload))
        return results

    async def archive(self, product_id: str) -> AgriculturalProduct:
        return await self.update(product_id, status=AvailabilityStatus.ARCHIVED)

    async def restore(self, product_id: str) -> AgriculturalProduct:
        return await self.update(product_id, status=AvailabilityStatus.AVAILABLE)

    def find_duplicates(self, product_id: str) -> list[AgriculturalProduct]:
        product = self.get(product_id)
        return self._duplicates.find_duplicates(product, self._store.agro_products.list_all())

    def create_category(self, category: ProductCategory) -> ProductCategory:
        return self._store.categories.save(category.category_id, category)

    def list_categories(self) -> list[ProductCategory]:
        return self._store.categories.list_all()

    def set_attributes(self, product_id: str, attributes: dict[str, Any]) -> AgriculturalProduct:
        product = self.get(product_id)
        product.attributes.update(attributes)
        product.updated_at = time.time()
        saved = self._store.agro_products.save(product_id, product)
        self._sync_legacy(saved)
        return saved

    def create_crop(self, crop: Crop) -> Crop:
        return self._store.crop_records.save(crop.crop_id, crop)

    def list_crops(self) -> list[Crop]:
        return self._store.crop_records.list_all()

    def create_variety(self, variety: CropVariety) -> CropVariety:
        if variety.crop_id and self._store.crop_records.get(variety.crop_id) is None:
            raise NotFoundError("Crop", variety.crop_id)
        return self._store.crop_varieties.save(variety.variety_id, variety)

    def create_packaging(self, packaging: Packaging) -> Packaging:
        return self._store.packaging.save(packaging.packaging_id, packaging)

    async def recommend(self, product_id: str, *, limit: int = 5) -> list[dict[str, Any]]:
        product = self.get(product_id)
        return await self._ai.recommend_products(product, self.list_products(), limit=limit)


product_catalog_service = ProductCatalogService()
