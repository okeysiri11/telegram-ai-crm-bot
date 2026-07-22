# Port ERP AI operations REST handlers — Sprint 9.6.

from __future__ import annotations

from aiohttp import web

from applications.port_erp import port_erp
from applications.port_erp.api.middleware import error_response, json_response
from applications.port_erp.digital_twin.models import AlertSeverity
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError


async def digital_twin_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "ai_operations_engine": port_erp.config.ai_operations_engine,
            "application_version": port_erp.config.application_version,
            "metrics": port_erp.ai_ops.metrics(),
            "state": port_erp.ai_ops.twin.state(),
        }
    )


async def digital_twin_snapshot_handler(request: web.Request) -> web.Response:
    port_id = request.query.get("port_id", "")
    snap = await port_erp.ai_ops.twin.snapshot(port_id=port_id)
    return json_response(snap.to_dict(), status=201)


async def digital_twin_list_handler(request: web.Request) -> web.Response:
    limit = int(request.query.get("limit", 20) or 20)
    return json_response({"items": [s.to_dict() for s in port_erp.ai_ops.twin.list_snapshots(limit=limit)]})


async def digital_twin_weather_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        weather = port_erp.ai_ops.twin.set_weather(
            condition=data.get("condition", "clear"),
            wind_knots=float(data.get("wind_knots", 0) or 0),
            visibility_km=float(data.get("visibility_km", 10) or 10),
            temperature_c=float(data.get("temperature_c", 25) or 25),
        )
        return json_response(weather.to_dict())
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def dashboard_handler(_request: web.Request) -> web.Response:
    return json_response(port_erp.ai_ops.dashboard.dashboard())


async def operations_center_handler(_request: web.Request) -> web.Response:
    return json_response(port_erp.ai_ops.operations.overview())


async def operations_refresh_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        data = {}
    result = await port_erp.ai_ops.operations.refresh(port_id=(data or {}).get("port_id", ""))
    return json_response(result)


async def operations_alerts_handler(request: web.Request) -> web.Response:
    sev = request.query.get("severity")
    items = port_erp.ai_ops.alerts.list_alerts(
        severity=AlertSeverity(sev) if sev else None,
        acknowledged=False if request.query.get("open") == "1" else None,
    )
    return json_response({"items": [a.to_dict() for a in items], "types": port_erp.ai_ops.alerts.alert_types()})


async def operations_alert_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        alert = await port_erp.ai_ops.alerts.raise_alert(
            alert_type=data.get("alert_type", "capacity_threshold"),
            title=data.get("title", ""),
            message=data.get("message", ""),
            severity=data.get("severity", "warning"),
            related_id=data.get("related_id", ""),
        )
        return json_response(alert.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def operations_alert_ack_handler(request: web.Request) -> web.Response:
    try:
        alert = port_erp.ai_ops.alerts.acknowledge(request.match_info["alert_id"])
        return json_response(alert.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def simulation_scenarios_handler(_request: web.Request) -> web.Response:
    return json_response({"items": port_erp.ai_ops.simulation.scenarios()})


async def simulation_run_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        run = await port_erp.ai_ops.simulation.run(
            data.get("scenario", "peak_season"),
            name=data.get("name", ""),
            parameters=data.get("parameters") or {},
        )
        return json_response(run.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def simulation_list_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [r.to_dict() for r in port_erp.ai_ops.simulation.list_runs()]})


async def optimization_run_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        data = {}
    plans = await port_erp.ai_ops.optimization.run_all(
        vessel_id=(data or {}).get("vessel_id", ""),
        terminal_id=(data or {}).get("terminal_id", ""),
    )
    return json_response({"items": [p.to_dict() for p in plans]})


async def optimization_list_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [p.to_dict() for p in port_erp.ai_ops.optimization.list_plans()]})


async def optimization_berth_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        data = {}
    plan = await port_erp.ai_ops.optimization.berths.allocate(
        vessel_id=(data or {}).get("vessel_id", ""),
        prefer_terminal_id=(data or {}).get("terminal_id", ""),
    )
    return json_response(plan.to_dict(), status=201)


async def optimization_yard_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        data = {}
    plan = await port_erp.ai_ops.optimization.yard.optimize_flow(
        terminal_id=(data or {}).get("terminal_id", "")
    )
    return json_response(plan.to_dict(), status=201)


async def executive_briefing_handler(_request: web.Request) -> web.Response:
    briefing = await port_erp.ai_ops.executive.briefing()
    return json_response(briefing)


async def executive_recommendations_handler(_request: web.Request) -> web.Response:
    recs = port_erp.ai_ops.decisions.recommend()
    return json_response({"items": [r.to_dict() for r in recs]})


async def executive_predictions_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "queue": port_erp.ai_ops.prediction.predict_queue().to_dict(),
            "congestion": port_erp.ai_ops.prediction.predict_congestion().to_dict(),
            "dwell": port_erp.ai_ops.prediction.predict_dwell_time().to_dict(),
            "eta_accuracy": port_erp.ai_ops.prediction.eta_accuracy().to_dict(),
        }
    )
