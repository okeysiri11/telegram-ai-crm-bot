# CatalogService — categories and marketplace listings.

from __future__ import annotations

from applications.agro_marketplace.shared.exceptions import NotFoundError
from applications.agro_marketplace.shared.models import MarketplaceListing, ProductCategory, ProductStatus
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class CatalogService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def list_categories(self) -> list[ProductCategory]:
        return self._store.categories.list_all()

    def create_category(self, category: ProductCategory) -> ProductCategory:
        return self._store.categories.save(category.category_id, category)

    def get_category(self, category_id: str) -> ProductCategory:
        category = self._store.categories.get(category_id)
        if category is None:
            raise NotFoundError("ProductCategory", category_id)
        return category

    def create_listing(self, listing: MarketplaceListing) -> MarketplaceListing:
        product = self._store.products.get(listing.product_id)
        if product is None:
            raise NotFoundError("Product", listing.product_id)
        product.status = ProductStatus.LISTED
        self._store.products.save(product.product_id, product)
        return self._store.listings.save(listing.listing_id, listing)

    def list_listings(self, *, active_only: bool = True) -> list[MarketplaceListing]:
        items = self._store.listings.list_all()
        if active_only:
            items = [i for i in items if i.is_active]
        return items

    def search(self, *, query: str = "", category_id: str = "") -> list[dict]:
        products = self._store.products.list_all()
        results = []
        for product in products:
            if product.status != ProductStatus.LISTED:
                continue
            if category_id and product.category_id != category_id:
                continue
            if query and query.lower() not in product.name.lower():
                continue
            results.append(product.to_dict())
        return results


catalog_service = CatalogService()
