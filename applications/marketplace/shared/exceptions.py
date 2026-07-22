from __future__ import annotations


class MarketplaceError(Exception):
    pass


class NotFoundError(MarketplaceError):
    def __init__(self, entity: str, entity_id: str) -> None:
        super().__init__(f"{entity} not found: {entity_id}")
        self.entity = entity
        self.entity_id = entity_id


class ValidationError(MarketplaceError):
    pass


class CompatibilityError(MarketplaceError):
    pass
