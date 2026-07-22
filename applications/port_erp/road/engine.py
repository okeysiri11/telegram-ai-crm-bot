# Mode abstractions — sea / road / rail / air legs.

from __future__ import annotations

from applications.port_erp.multimodal.models import RouteLeg, TransportMode
from applications.port_erp.shared.exceptions import ValidationError


def build_leg(
    *,
    mode: TransportMode,
    from_hub_id: str,
    to_hub_id: str,
    distance_km: float = 0.0,
    duration_hours: float = 0.0,
    cost: float = 0.0,
    carrier_id: str = "",
) -> RouteLeg:
    if not from_hub_id or not to_hub_id:
        raise ValidationError("from_hub_id and to_hub_id are required")
    return RouteLeg(
        from_hub_id=from_hub_id,
        to_hub_id=to_hub_id,
        mode=mode,
        distance_km=distance_km,
        duration_hours=duration_hours,
        cost=cost,
        carrier_id=carrier_id,
    )


class RoadTransportEngine:
    mode = TransportMode.ROAD

    def create_leg(self, **kwargs) -> RouteLeg:
        return build_leg(mode=self.mode, **kwargs)


class RailTransportEngine:
    mode = TransportMode.RAIL

    def create_leg(self, **kwargs) -> RouteLeg:
        return build_leg(mode=self.mode, **kwargs)


class AirTransportEngine:
    """Air transport abstraction for multimodal planning."""

    mode = TransportMode.AIR

    def create_leg(self, **kwargs) -> RouteLeg:
        return build_leg(mode=self.mode, **kwargs)


class SeaTransportEngine:
    mode = TransportMode.SEA

    def create_leg(self, **kwargs) -> RouteLeg:
        return build_leg(mode=self.mode, **kwargs)


road_transport_engine = RoadTransportEngine()
rail_transport_engine = RailTransportEngine()
air_transport_engine = AirTransportEngine()
sea_transport_engine = SeaTransportEngine()
