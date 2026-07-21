# Register Port ERP API routes on aiohttp application.

from __future__ import annotations

from aiohttp import web

from applications.port_erp.api import handlers, tracking_handlers
from applications.port_erp.api.middleware import auth_middleware
from applications.port_erp.config import DEFAULT_CONFIG


def register_port_erp_routes(app: web.Application) -> None:
    """Mount REST routes for Port ERP under /api/port/v1."""
    config = DEFAULT_CONFIG
    prefix = config.api_prefix

    app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_get(f"{prefix}/roles", handlers.roles_handler)

    app.router.add_get(f"{prefix}/ports", handlers.list_ports_handler)
    app.router.add_post(f"{prefix}/ports", handlers.create_port_handler)
    app.router.add_get(f"{prefix}/ports/{{port_id}}", handlers.get_port_handler)

    app.router.add_get(f"{prefix}/terminals", handlers.list_terminals_handler)
    app.router.add_post(f"{prefix}/terminals", handlers.create_terminal_handler)

    app.router.add_get(f"{prefix}/berths", handlers.list_berths_handler)
    app.router.add_post(f"{prefix}/berths", handlers.create_berth_handler)
    app.router.add_post(f"{prefix}/berths/{{berth_id}}/assign", handlers.assign_berth_handler)

    app.router.add_get(f"{prefix}/vessels", handlers.list_vessels_handler)
    app.router.add_post(f"{prefix}/vessels", handlers.create_vessel_handler)
    app.router.add_get(f"{prefix}/vessels/positions", tracking_handlers.list_vessel_positions_handler)
    app.router.add_post(
        f"{prefix}/vessels/{{vessel_id}}/position",
        tracking_handlers.vessel_position_handler,
    )
    app.router.add_get(
        f"{prefix}/vessels/{{vessel_id}}/position",
        tracking_handlers.vessel_live_position_handler,
    )
    app.router.add_post(f"{prefix}/voyages", handlers.create_voyage_handler)
    app.router.add_post(f"{prefix}/voyages/{{voyage_id}}/arrive", handlers.voyage_arrive_handler)
    app.router.add_post(f"{prefix}/voyages/{{voyage_id}}/depart", handlers.voyage_depart_handler)

    app.router.add_get(f"{prefix}/containers", handlers.list_containers_handler)
    app.router.add_post(f"{prefix}/containers", handlers.create_container_handler)
    app.router.add_get(f"{prefix}/containers/statuses", tracking_handlers.container_statuses_handler)
    app.router.add_post(
        f"{prefix}/containers/{{container_id}}/receive",
        handlers.receive_container_handler,
    )
    app.router.add_post(
        f"{prefix}/containers/{{container_id}}/position",
        tracking_handlers.container_position_handler,
    )
    app.router.add_post(
        f"{prefix}/containers/{{container_id}}/lifecycle",
        tracking_handlers.container_lifecycle_handler,
    )
    app.router.add_get(
        f"{prefix}/containers/{{container_id}}/history",
        tracking_handlers.container_history_handler,
    )

    app.router.add_get(f"{prefix}/cargo", handlers.list_cargo_handler)
    app.router.add_post(f"{prefix}/cargo", handlers.create_cargo_handler)

    app.router.add_get(f"{prefix}/customers", handlers.list_customers_handler)
    app.router.add_post(f"{prefix}/customers", handlers.create_customer_handler)

    app.router.add_get(f"{prefix}/companies", handlers.list_companies_handler)
    app.router.add_post(f"{prefix}/companies/shipping-lines", handlers.create_shipping_line_handler)
    app.router.add_post(f"{prefix}/companies/forwarders", handlers.create_forwarder_handler)
    app.router.add_post(f"{prefix}/companies/brokers", handlers.create_broker_handler)
    app.router.add_post(f"{prefix}/companies/carriers", handlers.create_carrier_handler)
    app.router.add_post(f"{prefix}/companies/operators", handlers.create_operator_handler)

    app.router.add_get(f"{prefix}/operations", handlers.operations_metrics_handler)
    app.router.add_post(f"{prefix}/operations/warehouses", handlers.create_warehouse_handler)
    app.router.add_post(f"{prefix}/operations/gates", handlers.create_gate_handler)
    app.router.add_post(f"{prefix}/operations/gates/{{gate_id}}/open", handlers.open_gate_handler)
    app.router.add_post(f"{prefix}/operations/gates/{{gate_id}}/close", handlers.close_gate_handler)

    # Sprint 9.2 — live tracking
    app.router.add_get(f"{prefix}/tracking", tracking_handlers.tracking_health_handler)
    app.router.add_get(f"{prefix}/tracking/live", tracking_handlers.tracking_live_handler)
    app.router.add_get(f"{prefix}/tracking/fleet", tracking_handlers.tracking_fleet_handler)
    app.router.add_get(
        f"{prefix}/tracking/routes/{{asset_type}}/{{asset_id}}",
        tracking_handlers.tracking_route_handler,
    )
    app.router.add_post(f"{prefix}/tracking/eta", tracking_handlers.tracking_predict_eta_handler)

    app.router.add_get(f"{prefix}/gps/trucks", tracking_handlers.gps_list_trucks_handler)
    app.router.add_post(f"{prefix}/gps/trucks", tracking_handlers.gps_register_truck_handler)
    app.router.add_post(
        f"{prefix}/gps/trucks/{{truck_id}}/position",
        tracking_handlers.gps_truck_position_handler,
    )
    app.router.add_post(
        f"{prefix}/gps/rail/{{rail_id}}/position",
        tracking_handlers.gps_rail_position_handler,
    )

    app.router.add_get(f"{prefix}/maps", tracking_handlers.maps_viewport_handler)
    app.router.add_get(f"{prefix}/maps/geofences", tracking_handlers.maps_list_geofences_handler)
    app.router.add_post(f"{prefix}/maps/geofences", tracking_handlers.maps_create_geofence_handler)

    app.router.add_get(f"{prefix}/timeline", tracking_handlers.timeline_recent_handler)
    app.router.add_get(
        f"{prefix}/timeline/{{asset_type}}/{{asset_id}}",
        tracking_handlers.timeline_asset_handler,
    )
