# Operations API handlers — Sprint 6.8.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import json_response


async def ops_health_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.production_engine.monitoring.health_probe())


async def ops_readiness_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.production_engine.monitoring.readiness_probe())


async def ops_liveness_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.production_engine.monitoring.liveness_probe())


async def ops_metrics_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.production_engine.metrics())


async def release_report_handler(_request: web.Request) -> web.Response:
    report = await auto_marketplace.production_engine.generate_release_report()
    return json_response(report.to_dict())


async def release_manifest_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.production_engine.release_manifest())


async def deployment_checklist_handler(_request: web.Request) -> web.Response:
    return json_response({"items": auto_marketplace.production_engine.go_live_checklist()})


async def deployment_preflight_handler(request: web.Request) -> web.Response:
    version = request.query.get("version", "1.1.0-alpha")
    return json_response(auto_marketplace.production_engine.deployment.preflight(version=version))


async def rollback_procedure_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.production_engine.deployment.rollback_procedure())


async def backup_create_handler(_request: web.Request) -> web.Response:
    snapshot = auto_marketplace.production_engine.backups.create_snapshot()
    return json_response(snapshot, status=201)


async def backup_procedures_handler(_request: web.Request) -> web.Response:
    return json_response({
        "backup": auto_marketplace.production_engine.backups.backup_procedure(),
        "restore": auto_marketplace.production_engine.backups.restore_procedure(),
    })


async def maintenance_status_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.production_engine.maintenance.status())


async def maintenance_enable_handler(request: web.Request) -> web.Response:
    data = await request.json() if request.can_read_body else {}
    return json_response(auto_marketplace.production_engine.maintenance.enable(message=data.get("message", "")))


async def maintenance_disable_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.production_engine.maintenance.disable())


async def support_guide_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.production_engine.support.guide())


async def admin_guide_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.production_engine.support.administrator_guide())


async def user_guide_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.production_engine.support.user_guide())


async def incident_guide_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.production_engine.monitoring.incident_guide())


async def observability_handler(_request: web.Request) -> web.Response:
    result = await auto_marketplace.production_engine.monitoring.integrate_observability()
    return json_response(result)
