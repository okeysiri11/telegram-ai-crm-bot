# LogisticsEngine — planning, warehouse dispatch, delivery scheduling.

from __future__ import annotations

import time
from typing import Any

from applications.agro_marketplace.containers.service import ContainersService, containers_service
from applications.agro_marketplace.export.ai_integration import ExportAIIntegration, export_ai
from applications.agro_marketplace.export.engine import ExportEngine, export_engine
from applications.agro_marketplace.export.models import Container, FreightOrder, InternationalExportShipment
from applications.agro_marketplace.ports.service import PortsService, ports_service
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.models import Delivery, DeliveryStatus
from applications.agro_marketplace.shared.store import AgroStore, agro_store
from applications.agro_marketplace.shipping.service import ShippingService, shipping_service
from applications.agro_marketplace.warehouse.engine import WarehouseEngine, warehouse_engine


class LogisticsEngine:
    def __init__(
        self,
        store: AgroStore | None = None,
        export: ExportEngine | None = None,
        shipping: ShippingService | None = None,
        ports: PortsService | None = None,
        containers: ContainersService | None = None,
        warehouses: WarehouseEngine | None = None,
        ai: ExportAIIntegration | None = None,
    ) -> None:
        self._store = store or agro_store
        self._export = export or export_engine
        self.shipping = shipping or shipping_service
        self.ports = ports or ports_service
        self.containers = containers or containers_service
        self.warehouses = warehouses or warehouse_engine
        self._ai = ai or export_ai

    async def plan_shipment(
        self,
        shipment: InternationalExportShipment,
        *,
        estimated_days: int = 18,
    ) -> dict[str, Any]:
        if shipment.origin_port_id and shipment.destination_port_id:
            route = await self.shipping.plan_route(
                origin_port_id=shipment.origin_port_id,
                destination_port_id=shipment.destination_port_id,
                estimated_days=estimated_days,
            )
            shipment.route_id = route.route_id
            shipment.estimated_arrival = time.time() + estimated_days * 86400
        carriers = await self.shipping.recommend_carriers(shipment.destination_country)
        if carriers and not shipment.carrier_id:
            shipment.carrier_id = carriers[0]["carrier_id"]
        optimization = await self._ai.optimize_shipment(shipment)
        prediction = await self._ai.predict_delivery(
            shipment,
            self.shipping.get_route(shipment.route_id) if shipment.route_id else None,
        )
        saved = await self._export.create_shipment(shipment)
        return {
            "shipment": saved.to_dict(),
            "carriers": carriers,
            "optimization": optimization,
            "delivery_prediction": prediction,
        }

    async def warehouse_dispatch(
        self,
        *,
        shipment_id: str,
        warehouse_id: str,
        quantity_tons: float,
        product_id: str = "",
    ) -> dict[str, Any]:
        shipment = self._export.get_shipment(shipment_id)
        warehouse = self.warehouses.get_warehouse(warehouse_id)
        container = self.containers.create_container(Container(status="reserved"))
        load = await self.containers.load_container(
            container_id=container.container_id,
            shipment_id=shipment_id,
            product_id=product_id,
            quantity_tons=quantity_tons,
        )
        shipment.warehouse_id = warehouse_id
        if container.container_id not in shipment.container_ids:
            shipment.container_ids.append(container.container_id)
        shipment.updated_at = time.time()
        self._store.intl_shipments.save(shipment_id, shipment)
        if warehouse.used_tons > 0:
            self.warehouses.adjust_capacity_usage(
                warehouse_id,
                -min(quantity_tons, warehouse.used_tons),
            )
        return {"shipment_id": shipment_id, "load": load.to_dict(), "container": container.to_dict()}

    def schedule_delivery(self, delivery: Delivery) -> Delivery:
        delivery.status = DeliveryStatus.SCHEDULED
        return self._store.deliveries.save(delivery.delivery_id, delivery)

    def book_freight(
        self,
        *,
        shipment_id: str,
        carrier_id: str,
        route_id: str = "",
        cost: float = 0.0,
    ) -> FreightOrder:
        self._export.get_shipment(shipment_id)
        self.shipping.get_carrier(carrier_id)
        return self.shipping.book_freight(
            FreightOrder(
                shipment_id=shipment_id,
                carrier_id=carrier_id,
                route_id=route_id,
                cost=cost,
            )
        )

    def metrics(self) -> dict[str, Any]:
        return {
            "ports": self._store.ports.count(),
            "carriers": self._store.carriers.count(),
            "routes": self._store.route_plans.count(),
            "freight_orders": self._store.freight_orders.count(),
            "deliveries": self._store.deliveries.count(),
        }


logistics_engine = LogisticsEngine()
