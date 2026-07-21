# Ops / release API handlers — Sprint 8.8.

from __future__ import annotations

from aiohttp import web

from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.api.middleware import json_response


async def ops_health_handler(_request: web.Request) -> web.Response:
    return json_response(agro_marketplace.ops.health())


async def ops_version_handler(_request: web.Request) -> web.Response:
    return json_response(agro_marketplace.ops.version_info())


async def ops_readiness_handler(_request: web.Request) -> web.Response:
    snapshot = await agro_marketplace.ops.readiness()
    return json_response(snapshot.to_dict())


async def ops_validation_handler(_request: web.Request) -> web.Response:
    report = await agro_marketplace.ops.validation.run_full_validation()
    return json_response(report.to_dict())


async def ops_release_handler(request: web.Request) -> web.Response:
    data = {}
    try:
        data = await request.json()
    except Exception:
        data = {}
    if request.method == "GET":
        items = agro_marketplace.ops.list_releases()
        return json_response({"items": [r.to_dict() for r in items]})
    bundle = await agro_marketplace.ops.production_bundle()
    if data.get("notes"):
        release = await agro_marketplace.ops.create_release(notes=data["notes"])
        bundle["release"] = release.to_dict()
    return json_response(bundle, status=201)


async def ops_reports_handler(request: web.Request) -> web.Response:
    kind = request.query.get("kind")
    qa = agro_marketplace.ops.qa
    mapping = {
        "quality": qa.quality_report,
        "security": qa.security_report,
        "performance": qa.performance_report,
        "compatibility": qa.compatibility_report,
        "deployment": qa.deployment_report,
    }
    if kind and kind in mapping:
        return json_response(mapping[kind]().to_dict())
    if kind == "production":
        report = await agro_marketplace.ops.validation.run_full_validation()
        return json_response(report.to_dict())
    return json_response(
        {
            "quality": qa.quality_report().to_dict(),
            "security": qa.security_report().to_dict(),
            "performance": qa.performance_report().to_dict(),
            "compatibility": qa.compatibility_report().to_dict(),
            "deployment": qa.deployment_report().to_dict(),
        }
    )


async def ops_certify_handler(_request: web.Request) -> web.Response:
    record = await agro_marketplace.ops.certify()
    return json_response(record.to_dict(), status=201)


async def ops_deploy_verify_handler(_request: web.Request) -> web.Response:
    result = await agro_marketplace.ops.verify_deployment()
    return json_response(result)
