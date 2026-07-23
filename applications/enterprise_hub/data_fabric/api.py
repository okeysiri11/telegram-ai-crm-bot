"""API handlers — Enterprise Unified Data Fabric (Sprint 20.7)."""

from __future__ import annotations

from aiohttp import web

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.middleware import json_response
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError


async def _read_json(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, NotFoundError):
        return json_response({"error": str(exc)}, status=404)
    if isinstance(exc, ValidationError):
        return json_response({"error": str(exc)}, status=400)
    return json_response({"error": str(exc)}, status=500)


def _suite():
    return enterprise_hub.data_fabric


async def edf_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "data_fabric_ready": health.get("data_fabric_ready"),
            "data_catalog_ready": health.get("data_catalog_ready"),
            "federation_ready": health.get("federation_ready"),
            "data_governance_ready": health.get("data_governance_ready"),
            "suite": _suite().status(),
        }
    )


async def edf_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def edf_catalog_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            q = request.rel_url.query.get("q", "")
            kind = request.rel_url.query.get("kind")
            return json_response({"assets": suite.catalog.search(query=q, kind=kind), **suite.catalog.status()})
        body = await _read_json(request)
        return json_response(
            suite.catalog.register(
                name=body.get("name", ""),
                kind=body.get("kind", "table"),
                source=body.get("source", "custom"),
                owner=body.get("owner", "data-ops"),
                description=body.get("description", ""),
                tags=body.get("tags") if isinstance(body.get("tags"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edf_query_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().core.unified_query(
                query=body.get("query", ""),
                sources=body.get("sources") if isinstance(body.get("sources"), list) else None,
                principal=body.get("principal", "system"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edf_federation_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().federation.federate(
                sources=body.get("sources") if isinstance(body.get("sources"), list) else None,
                query=body.get("query", ""),
                join_key=body.get("join_key", "entity_id"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edf_governance_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(suite.governance.status())
        body = await _read_json(request)
        return json_response(
            suite.governance.enforce(
                asset_id=body.get("asset_id", ""),
                principal=body.get("principal", "system"),
                retain_days=int(body.get("retain_days", 365) or 365),
                mask_fields=body.get("mask_fields") if isinstance(body.get("mask_fields"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edf_lineage_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(suite.lineage.status())
        body = await _read_json(request)
        return json_response(
            suite.lineage.record(
                asset_id=body.get("asset_id", ""),
                upstream=body.get("upstream") if isinstance(body.get("upstream"), list) else None,
                transforms=body.get("transforms") if isinstance(body.get("transforms"), list) else None,
                consumers=body.get("consumers") if isinstance(body.get("consumers"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edf_quality_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(suite.quality.status())
        body = await _read_json(request)
        return json_response(
            suite.quality.assess(
                asset_id=body.get("asset_id", ""),
                metrics=body.get("metrics") if isinstance(body.get("metrics"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edf_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def edf_analytics_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        return json_response(
            {
                "usage": suite.usage.report(),
                "quality": suite.quality_analytics.report(),
                "optimization": suite.optimization.report(),
            }
        )
    except Exception as exc:
        return _handle_error(exc)
