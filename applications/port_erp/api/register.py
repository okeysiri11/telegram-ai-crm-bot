# Register Port ERP API routes on aiohttp application.

from __future__ import annotations

from aiohttp import web

from applications.port_erp.api import handlers
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
    app.router.add_post(f"{prefix}/voyages", handlers.create_voyage_handler)
    app.router.add_post(f"{prefix}/voyages/{{voyage_id}}/arrive", handlers.voyage_arrive_handler)
    app.router.add_post(f"{prefix}/voyages/{{voyage_id}}/depart", handlers.voyage_depart_handler)

    app.router.add_get(f"{prefix}/containers", handlers.list_containers_handler)
    app.router.add_post(f"{prefix}/containers", handlers.create_container_handler)
    app.router.add_post(
        f"{prefix}/containers/{{container_id}}/receive",
        handlers.receive_container_handler,
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
