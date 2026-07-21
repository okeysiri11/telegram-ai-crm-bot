# Duplicate detection for agricultural products.

from __future__ import annotations

from applications.agro_marketplace.product_catalog.models import AgriculturalProduct


class DuplicateDetector:
    def find_duplicates(
        self,
        product: AgriculturalProduct,
        existing: list[AgriculturalProduct],
    ) -> list[AgriculturalProduct]:
        matches: list[AgriculturalProduct] = []
        sku = product.sku.strip().lower()
        for item in existing:
            if item.product_id == product.product_id:
                continue
            if item.status.value == "archived":
                continue
            if sku and item.sku.strip().lower() == sku:
                matches.append(item)
                continue
            if (
                item.name.strip().lower() == product.name.strip().lower()
                and item.farmer_id == product.farmer_id
                and item.crop_id == product.crop_id
                and item.region.strip().lower() == product.region.strip().lower()
            ):
                matches.append(item)
        return matches

    def is_duplicate(self, product: AgriculturalProduct, existing: list[AgriculturalProduct]) -> bool:
        return bool(self.find_duplicates(product, existing))


duplicate_detector = DuplicateDetector()
