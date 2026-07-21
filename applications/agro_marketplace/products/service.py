# ProductService — products, crops, harvests.

from __future__ import annotations

import time

from events.publisher import publish

from applications.agro_marketplace.shared.events import HarvestAddedEvent, ProductCreatedEvent
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.models import Crop, Harvest, Product, ProductStatus
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class ProductService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def list_products(self, *, status: ProductStatus | None = None) -> list[Product]:
        items = self._store.products.list_all()
        if status:
            items = [p for p in items if p.status == status]
        return items

    def get_product(self, product_id: str) -> Product:
        product = self._store.products.get(product_id)
        if product is None:
            raise NotFoundError("Product", product_id)
        return product

    async def create_product(self, product: Product) -> Product:
        if not product.name:
            raise ValidationError("name is required")
        product.updated_at = time.time()
        saved = self._store.products.save(product.product_id, product)
        await publish(
            ProductCreatedEvent(
                product_id=saved.product_id,
                farmer_id=saved.farmer_id,
                name=saved.name,
            )
        )
        return saved

    def update_product(self, product_id: str, **updates: object) -> Product:
        product = self.get_product(product_id)
        for key, value in updates.items():
            if hasattr(product, key) and value is not None:
                setattr(product, key, value)
        product.updated_at = time.time()
        return self._store.products.save(product_id, product)

    def create_crop(self, crop: Crop) -> Crop:
        return self._store.crops.save(crop.crop_id, crop)

    def list_crops(self) -> list[Crop]:
        return self._store.crops.list_all()

    async def add_harvest(self, harvest: Harvest) -> Harvest:
        if harvest.quantity_tons <= 0:
            raise ValidationError("quantity_tons must be positive")
        saved = self._store.harvests.save(harvest.harvest_id, harvest)
        await publish(
            HarvestAddedEvent(
                harvest_id=saved.harvest_id,
                farm_id=saved.farm_id,
                crop_id=saved.crop_id,
                quantity_tons=saved.quantity_tons,
            )
        )
        return saved

    def list_harvests(self, *, farm_id: str | None = None) -> list[Harvest]:
        items = self._store.harvests.list_all()
        if farm_id:
            items = [h for h in items if h.farm_id == farm_id]
        return items


product_service = ProductService()
