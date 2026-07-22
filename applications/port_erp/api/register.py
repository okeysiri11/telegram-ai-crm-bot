# Register Port ERP API routes on aiohttp application.

from __future__ import annotations

from aiohttp import web

from applications.port_erp.api import (
    ai_ops_handlers,
    customs_handlers,
    finance_handlers,
    handlers,
    logistics_handlers,
    terminal_handlers,
    tracking_handlers,
)
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

    # Sprint 9.3 — terminal / warehouse / yard / gate / equipment / planning
    app.router.add_get(f"{prefix}/terminal", terminal_handlers.terminal_health_handler)
    app.router.add_get(f"{prefix}/terminal/storage/optimize", terminal_handlers.storage_optimize_handler)

    app.router.add_get(f"{prefix}/yard/blocks", terminal_handlers.yard_list_blocks_handler)
    app.router.add_post(f"{prefix}/yard/blocks", terminal_handlers.yard_create_block_handler)
    app.router.add_get(f"{prefix}/yard/slots", terminal_handlers.yard_list_slots_handler)
    app.router.add_post(f"{prefix}/yard/assign", terminal_handlers.yard_assign_handler)
    app.router.add_post(f"{prefix}/yard/relocate", terminal_handlers.yard_relocate_handler)
    app.router.add_post(f"{prefix}/yard/release", terminal_handlers.yard_release_handler)
    app.router.add_get(f"{prefix}/yard/density", terminal_handlers.yard_density_handler)

    app.router.add_get(f"{prefix}/warehouse", terminal_handlers.warehouse_list_handler)
    app.router.add_post(f"{prefix}/warehouse", terminal_handlers.warehouse_create_handler)
    app.router.add_post(f"{prefix}/warehouse/zones", terminal_handlers.warehouse_zone_handler)
    app.router.add_get(f"{prefix}/warehouse/inventory", terminal_handlers.warehouse_inventory_handler)
    app.router.add_post(f"{prefix}/warehouse/inventory", terminal_handlers.warehouse_inventory_handler)
    app.router.add_post(f"{prefix}/warehouse/tasks", terminal_handlers.warehouse_task_handler)
    app.router.add_post(
        f"{prefix}/warehouse/tasks/{{task_id}}/complete",
        terminal_handlers.warehouse_complete_task_handler,
    )
    app.router.add_post(f"{prefix}/warehouse/cycle-counts", terminal_handlers.warehouse_cycle_count_handler)
    app.router.add_post(f"{prefix}/warehouse/movements", terminal_handlers.warehouse_move_handler)

    app.router.add_get(f"{prefix}/gate", terminal_handlers.gate_list_handler)
    app.router.add_post(f"{prefix}/gate", terminal_handlers.gate_create_handler)
    app.router.add_post(f"{prefix}/gate/{{gate_id}}/open", terminal_handlers.gate_open_handler)
    app.router.add_post(f"{prefix}/gate/appointments", terminal_handlers.gate_appointment_handler)
    app.router.add_post(f"{prefix}/gate/check-in", terminal_handlers.gate_checkin_handler)
    app.router.add_post(f"{prefix}/gate/visits/{{visit_id}}/approve", terminal_handlers.gate_approve_handler)
    app.router.add_post(f"{prefix}/gate/visits/{{visit_id}}/reject", terminal_handlers.gate_reject_handler)
    app.router.add_post(f"{prefix}/gate/visits/{{visit_id}}/check-out", terminal_handlers.gate_checkout_handler)
    app.router.add_get(f"{prefix}/gate/{{gate_id}}/queue", terminal_handlers.gate_queue_handler)

    app.router.add_get(f"{prefix}/equipment", terminal_handlers.equipment_list_handler)
    app.router.add_post(f"{prefix}/equipment", terminal_handlers.equipment_create_handler)
    app.router.add_post(
        f"{prefix}/equipment/{{equipment_id}}/maintenance",
        terminal_handlers.equipment_maintenance_handler,
    )
    app.router.add_post(f"{prefix}/equipment/cranes/assign", terminal_handlers.crane_assign_handler)
    app.router.add_post(
        f"{prefix}/equipment/cranes/{{assignment_id}}/finish",
        terminal_handlers.crane_finish_handler,
    )
    app.router.add_post(f"{prefix}/equipment/dispatch", terminal_handlers.dispatch_create_handler)
    app.router.add_post(
        f"{prefix}/equipment/dispatch/{{job_id}}/assign",
        terminal_handlers.dispatch_assign_handler,
    )

    app.router.add_get(f"{prefix}/planning", terminal_handlers.planning_list_handler)
    app.router.add_post(f"{prefix}/planning", terminal_handlers.planning_create_handler)
    app.router.add_post(
        f"{prefix}/planning/{{plan_id}}/activate",
        terminal_handlers.planning_activate_handler,
    )

    # Sprint 9.4 — customs / documents / certificates / trade / broker / compliance
    app.router.add_get(f"{prefix}/customs", customs_handlers.customs_health_handler)
    app.router.add_get(f"{prefix}/customs/declarations", customs_handlers.customs_list_handler)
    app.router.add_post(f"{prefix}/customs/declarations", customs_handlers.customs_create_handler)
    app.router.add_post(
        f"{prefix}/customs/declarations/{{declaration_id}}/submit",
        customs_handlers.customs_submit_handler,
    )
    app.router.add_post(
        f"{prefix}/customs/declarations/{{declaration_id}}/hold",
        customs_handlers.customs_hold_handler,
    )
    app.router.add_post(
        f"{prefix}/customs/declarations/{{declaration_id}}/release",
        customs_handlers.customs_release_handler,
    )
    app.router.add_post(
        f"{prefix}/customs/declarations/{{declaration_id}}/complete",
        customs_handlers.customs_complete_handler,
    )
    app.router.add_get(f"{prefix}/customs/tariffs", customs_handlers.tariffs_list_handler)
    app.router.add_post(f"{prefix}/customs/tariffs", customs_handlers.tariffs_create_handler)

    app.router.add_get(f"{prefix}/documents", customs_handlers.documents_list_handler)
    app.router.add_post(f"{prefix}/documents", customs_handlers.documents_create_handler)
    app.router.add_get(f"{prefix}/documents/types", customs_handlers.documents_types_handler)
    app.router.add_post(
        f"{prefix}/documents/{{document_id}}/sign",
        customs_handlers.documents_sign_handler,
    )

    app.router.add_get(f"{prefix}/certificates", customs_handlers.certificates_list_handler)
    app.router.add_post(f"{prefix}/certificates", customs_handlers.certificates_create_handler)
    app.router.add_get(f"{prefix}/certificates/types", customs_handlers.certificates_types_handler)
    app.router.add_post(
        f"{prefix}/certificates/{{certificate_id}}/issue",
        customs_handlers.certificates_issue_handler,
    )

    app.router.add_get(f"{prefix}/trade", customs_handlers.trade_list_handler)
    app.router.add_post(f"{prefix}/trade", customs_handlers.trade_create_handler)
    app.router.add_get(f"{prefix}/trade/incoterms", customs_handlers.trade_incoterms_handler)
    app.router.add_get(f"{prefix}/trade/stages", customs_handlers.trade_stages_handler)
    app.router.add_post(
        f"{prefix}/trade/{{shipment_id}}/advance",
        customs_handlers.trade_advance_handler,
    )
    app.router.add_post(
        f"{prefix}/trade/{{shipment_id}}/customs",
        customs_handlers.trade_customs_handler,
    )
    app.router.add_post(
        f"{prefix}/trade/{{shipment_id}}/duties",
        customs_handlers.trade_duties_handler,
    )

    app.router.add_get(f"{prefix}/broker", customs_handlers.broker_list_handler)
    app.router.add_post(f"{prefix}/broker", customs_handlers.broker_create_handler)
    app.router.add_post(
        f"{prefix}/broker/{{case_id}}/clear",
        customs_handlers.broker_clear_handler,
    )

    app.router.add_get(f"{prefix}/compliance", customs_handlers.compliance_list_handler)
    app.router.add_post(f"{prefix}/compliance/evaluate", customs_handlers.compliance_evaluate_handler)

    # Sprint 9.5 — shipping / forwarders / carriers / routes / bookings / transport
    app.router.add_get(f"{prefix}/shipping", logistics_handlers.shipping_health_handler)
    app.router.add_get(f"{prefix}/shipping/lines", logistics_handlers.shipping_list_lines_handler)
    app.router.add_post(f"{prefix}/shipping/lines", logistics_handlers.shipping_create_line_handler)
    app.router.add_get(f"{prefix}/shipping/schedules", logistics_handlers.shipping_list_schedules_handler)
    app.router.add_post(f"{prefix}/shipping/schedules", logistics_handlers.shipping_create_schedule_handler)
    app.router.add_post(
        f"{prefix}/shipping/schedules/{{schedule_id}}/plan",
        logistics_handlers.shipping_plan_voyage_handler,
    )

    app.router.add_get(f"{prefix}/forwarders", logistics_handlers.forwarders_list_handler)
    app.router.add_post(f"{prefix}/forwarders", logistics_handlers.forwarders_create_handler)
    app.router.add_post(f"{prefix}/forwarders/consolidate", logistics_handlers.forwarders_consolidate_handler)

    app.router.add_get(f"{prefix}/carriers", logistics_handlers.carriers_list_handler)
    app.router.add_post(f"{prefix}/carriers", logistics_handlers.carriers_create_handler)
    app.router.add_post(f"{prefix}/carriers/contracts", logistics_handlers.carriers_contract_handler)

    app.router.add_get(f"{prefix}/routes", logistics_handlers.routes_list_handler)
    app.router.add_post(f"{prefix}/routes", logistics_handlers.routes_create_handler)
    app.router.add_get(f"{prefix}/routes/hubs", logistics_handlers.routes_list_hubs_handler)
    app.router.add_post(f"{prefix}/routes/hubs", logistics_handlers.routes_create_hub_handler)
    app.router.add_post(
        f"{prefix}/routes/{{route_id}}/optimize",
        logistics_handlers.routes_optimize_handler,
    )

    app.router.add_get(f"{prefix}/bookings", logistics_handlers.bookings_list_handler)
    app.router.add_post(f"{prefix}/bookings", logistics_handlers.bookings_create_handler)
    app.router.add_post(
        f"{prefix}/bookings/{{booking_id}}/quote",
        logistics_handlers.bookings_quote_handler,
    )
    app.router.add_post(
        f"{prefix}/bookings/{{booking_id}}/confirm",
        logistics_handlers.bookings_confirm_handler,
    )
    app.router.add_post(
        f"{prefix}/bookings/{{booking_id}}/execute",
        logistics_handlers.bookings_execute_handler,
    )
    app.router.add_post(
        f"{prefix}/bookings/{{booking_id}}/complete",
        logistics_handlers.bookings_complete_handler,
    )
    app.router.add_post(
        f"{prefix}/bookings/{{booking_id}}/cancel",
        logistics_handlers.bookings_cancel_handler,
    )

    app.router.add_get(f"{prefix}/transport", logistics_handlers.transport_list_handler)
    app.router.add_post(f"{prefix}/transport", logistics_handlers.transport_create_handler)
    app.router.add_post(
        f"{prefix}/transport/{{order_id}}/assign",
        logistics_handlers.transport_assign_handler,
    )
    app.router.add_post(
        f"{prefix}/transport/{{order_id}}/dispatch",
        logistics_handlers.transport_dispatch_handler,
    )
    app.router.add_post(
        f"{prefix}/transport/{{order_id}}/complete",
        logistics_handlers.transport_complete_handler,
    )
    app.router.add_post(
        f"{prefix}/transport/{{order_id}}/transfer",
        logistics_handlers.transport_transfer_handler,
    )

    # Sprint 9.6 — digital twin / dashboard / operations center / simulation / optimization / executive
    app.router.add_get(f"{prefix}/digital-twin", ai_ops_handlers.digital_twin_health_handler)
    app.router.add_post(f"{prefix}/digital-twin/snapshot", ai_ops_handlers.digital_twin_snapshot_handler)
    app.router.add_get(f"{prefix}/digital-twin/snapshots", ai_ops_handlers.digital_twin_list_handler)
    app.router.add_post(f"{prefix}/digital-twin/weather", ai_ops_handlers.digital_twin_weather_handler)

    app.router.add_get(f"{prefix}/dashboard", ai_ops_handlers.dashboard_handler)

    app.router.add_get(f"{prefix}/operations/center", ai_ops_handlers.operations_center_handler)
    app.router.add_post(f"{prefix}/operations/center/refresh", ai_ops_handlers.operations_refresh_handler)
    app.router.add_get(f"{prefix}/operations/alerts", ai_ops_handlers.operations_alerts_handler)
    app.router.add_post(f"{prefix}/operations/alerts", ai_ops_handlers.operations_alert_create_handler)
    app.router.add_post(
        f"{prefix}/operations/alerts/{{alert_id}}/acknowledge",
        ai_ops_handlers.operations_alert_ack_handler,
    )

    app.router.add_get(f"{prefix}/simulation", ai_ops_handlers.simulation_list_handler)
    app.router.add_get(f"{prefix}/simulation/scenarios", ai_ops_handlers.simulation_scenarios_handler)
    app.router.add_post(f"{prefix}/simulation/run", ai_ops_handlers.simulation_run_handler)

    app.router.add_get(f"{prefix}/optimization", ai_ops_handlers.optimization_list_handler)
    app.router.add_post(f"{prefix}/optimization/run", ai_ops_handlers.optimization_run_handler)
    app.router.add_post(f"{prefix}/optimization/berth", ai_ops_handlers.optimization_berth_handler)
    app.router.add_post(f"{prefix}/optimization/yard", ai_ops_handlers.optimization_yard_handler)

    app.router.add_get(f"{prefix}/executive", ai_ops_handlers.executive_briefing_handler)
    app.router.add_get(f"{prefix}/executive/recommendations", ai_ops_handlers.executive_recommendations_handler)
    app.router.add_get(f"{prefix}/executive/predictions", ai_ops_handlers.executive_predictions_handler)

    # Sprint 9.7 — finance / billing / contracts / tariffs / invoices / payments / accounting
    app.router.add_get(f"{prefix}/finance", finance_handlers.finance_health_handler)
    app.router.add_post(f"{prefix}/finance/expenses", finance_handlers.finance_expense_handler)
    app.router.add_get(f"{prefix}/finance/companies", finance_handlers.finance_companies_handler)
    app.router.add_post(f"{prefix}/finance/budgets", finance_handlers.finance_budget_handler)
    app.router.add_post(f"{prefix}/finance/accounts", finance_handlers.finance_customer_account_handler)
    app.router.add_post(f"{prefix}/finance/suppliers", finance_handlers.finance_supplier_handler)

    app.router.add_get(f"{prefix}/billing/fee-types", finance_handlers.billing_fee_types_handler)
    app.router.add_post(f"{prefix}/billing", finance_handlers.billing_create_handler)

    app.router.add_get(f"{prefix}/contracts", finance_handlers.contracts_list_handler)
    app.router.add_post(f"{prefix}/contracts", finance_handlers.contracts_create_handler)
    app.router.add_post(
        f"{prefix}/contracts/{{contract_id}}/activate",
        finance_handlers.contracts_activate_handler,
    )

    app.router.add_get(f"{prefix}/tariffs", finance_handlers.tariffs_list_handler)
    app.router.add_post(f"{prefix}/tariffs", finance_handlers.tariffs_create_handler)
    app.router.add_post(f"{prefix}/tariffs/quote", finance_handlers.tariffs_quote_handler)

    app.router.add_get(f"{prefix}/invoices", finance_handlers.invoices_list_handler)
    app.router.add_post(f"{prefix}/invoices", finance_handlers.invoices_create_handler)
    app.router.add_get(f"{prefix}/invoices/outstanding", finance_handlers.invoices_outstanding_handler)
    app.router.add_post(
        f"{prefix}/invoices/{{invoice_id}}/charges",
        finance_handlers.invoices_charge_handler,
    )
    app.router.add_post(
        f"{prefix}/invoices/{{invoice_id}}/issue",
        finance_handlers.invoices_issue_handler,
    )
    app.router.add_post(
        f"{prefix}/invoices/{{invoice_id}}/credit-notes",
        finance_handlers.invoices_credit_handler,
    )
    app.router.add_post(
        f"{prefix}/invoices/{{invoice_id}}/debit-notes",
        finance_handlers.invoices_debit_handler,
    )

    app.router.add_get(f"{prefix}/payments", finance_handlers.payments_list_handler)
    app.router.add_post(f"{prefix}/payments", finance_handlers.payments_create_handler)
    app.router.add_post(
        f"{prefix}/payments/{{payment_id}}/refund",
        finance_handlers.payments_refund_handler,
    )

    app.router.add_get(f"{prefix}/accounting", finance_handlers.accounting_journal_handler)
    app.router.add_post(f"{prefix}/accounting/entries", finance_handlers.accounting_post_handler)
    app.router.add_post(f"{prefix}/accounting/fx", finance_handlers.accounting_fx_handler)
    app.router.add_post(f"{prefix}/accounting/tax", finance_handlers.accounting_tax_handler)
