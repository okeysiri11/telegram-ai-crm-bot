# FarmerService — farmer, farm, and field management.

from __future__ import annotations

from events.publisher import publish

from applications.agro_marketplace.shared.events import FarmerRegisteredEvent
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.models import Farm, Farmer, Field
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class FarmerService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def list_farmers(self) -> list[Farmer]:
        return self._store.farmers.list_all()

    def get_farmer(self, farmer_id: str) -> Farmer:
        farmer = self._store.farmers.get(farmer_id)
        if farmer is None:
            raise NotFoundError("Farmer", farmer_id)
        return farmer

    async def register_farmer(self, farmer: Farmer) -> Farmer:
        if not farmer.name or not farmer.email:
            raise ValidationError("name and email are required")
        saved = self._store.farmers.save(farmer.farmer_id, farmer)
        await publish(
            FarmerRegisteredEvent(
                farmer_id=saved.farmer_id,
                email=saved.email,
                name=saved.name,
            )
        )
        return saved

    def create_farm(self, farm: Farm) -> Farm:
        self.get_farmer(farm.farmer_id)
        return self._store.farms.save(farm.farm_id, farm)

    def list_farms(self, *, farmer_id: str | None = None) -> list[Farm]:
        farms = self._store.farms.list_all()
        if farmer_id:
            farms = [f for f in farms if f.farmer_id == farmer_id]
        return farms

    def add_field(self, field: Field) -> Field:
        if self._store.farms.get(field.farm_id) is None:
            raise NotFoundError("Farm", field.farm_id)
        return self._store.fields.save(field.field_id, field)

    def list_fields(self, *, farm_id: str | None = None) -> list[Field]:
        fields = self._store.fields.list_all()
        if farm_id:
            fields = [f for f in fields if f.farm_id == farm_id]
        return fields


farmer_service = FarmerService()
