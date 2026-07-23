"""API handlers — Enterprise Data Platform & MDM (Sprint 19.7)."""

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
    return enterprise_hub.edp


async def edp_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "enterprise_data_platform_ready": health.get("enterprise_data_platform_ready"),
            "master_data_ready": health.get("master_data_ready"),
            "data_quality_ready": health.get("data_quality_ready"),
            "data_governance_ready": health.get("data_governance_ready"),
            "suite": _suite().status(),
        }
    )


async def edp_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def edp_master_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(suite.master.status())
        body = await _read_json(request)
        action = body.get("action", "upsert")
        if action == "relate":
            return json_response(
                suite.master.relate(
                    from_entity_id=body.get("from_entity_id", ""),
                    to_entity_id=body.get("to_entity_id", ""),
                    relation=body.get("relation", ""),
                ),
                status=201,
            )
        if action == "get":
            return json_response(suite.master.get(entity_id=body.get("entity_id", "")), status=200)
        return json_response(
            suite.manager.create_master(
                entity_type=body.get("entity_type", "company"),
                name=body.get("name", ""),
                attributes=body.get("attributes") if isinstance(body.get("attributes"), dict) else None,
                owner=body.get("owner", "system"),
                source=body.get("source", "mdm"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edp_catalog_handler(request: web.Request) -> web.Response:
    try:
        catalog = _suite().catalog
        if request.method == "GET":
            return json_response(catalog.status())
        body = await _read_json(request)
        return json_response(
            catalog.publish(
                name=body.get("name", ""),
                object_type=body.get("object_type", "entity"),
                owner=body.get("owner", "system"),
                source=body.get("source", "edp"),
                description=body.get("description", ""),
                schema_ref=body.get("schema", ""),
                links=body.get("links") if isinstance(body.get("links"), list) else None,
                version=body.get("version", "1.0"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edp_metadata_handler(request: web.Request) -> web.Response:
    try:
        metadata = _suite().metadata
        if request.method == "GET":
            return json_response(metadata.status())
        body = await _read_json(request)
        return json_response(
            metadata.register_schema(
                name=body.get("name", ""),
                entity_type=body.get("entity_type", ""),
                attributes=body.get("attributes") if isinstance(body.get("attributes"), list) else None,
                constraints=body.get("constraints") if isinstance(body.get("constraints"), list) else None,
                indexes=body.get("indexes") if isinstance(body.get("indexes"), list) else None,
                dependencies=body.get("dependencies") if isinstance(body.get("dependencies"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edp_quality_handler(request: web.Request) -> web.Response:
    try:
        quality = _suite().quality
        if request.method == "GET":
            return json_response(quality.status())
        body = await _read_json(request)
        action = body.get("action", "run")
        if action == "normalize":
            return json_response(
                quality.normalizer.normalize(
                    value=body.get("value", ""),
                    kind=body.get("kind", "text"),
                ),
                status=201,
            )
        if action == "rule":
            return json_response(
                quality.rules.evaluate(
                    rule=body.get("rule", "name_required"),
                    payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
                ),
                status=201,
            )
        return json_response(quality.run(entity_type=body.get("entity_type", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def edp_governance_handler(request: web.Request) -> web.Response:
    try:
        governance = _suite().governance
        if request.method == "GET":
            return json_response(governance.status())
        body = await _read_json(request)
        action = body.get("action", "policy")
        if action == "audit":
            return json_response(
                governance.audit(
                    entity_id=body.get("entity_id", ""),
                    actor=body.get("actor", ""),
                    action=body.get("audit_action", "change"),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        return json_response(
            governance.set_policy(
                entity_id=body.get("entity_id", ""),
                classification=body.get("classification", "internal"),
                retention_days=int(body.get("retention_days", 365) or 365),
                access=body.get("access") if isinstance(body.get("access"), list) else None,
                lifecycle=body.get("lifecycle", "active"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edp_lineage_handler(request: web.Request) -> web.Response:
    try:
        lineage = _suite().lineage
        if request.method == "GET":
            return json_response(lineage.status())
        body = await _read_json(request)
        return json_response(
            lineage.record(
                entity_id=body.get("entity_id", ""),
                source=body.get("source", ""),
                actor=body.get("actor", "system"),
                process=body.get("process", ""),
                ai_agent=body.get("ai_agent", ""),
                integration=body.get("integration", ""),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edp_versioning_handler(request: web.Request) -> web.Response:
    try:
        versioning = _suite().versioning
        if request.method == "GET":
            return json_response(versioning.status())
        body = await _read_json(request)
        action = body.get("action", "snapshot")
        if action == "compare":
            return json_response(
                versioning.compare(
                    version_id_a=body.get("version_id_a", ""),
                    version_id_b=body.get("version_id_b", ""),
                ),
                status=201,
            )
        if action == "rollback":
            return json_response(versioning.rollback(version_id=body.get("version_id", "")), status=201)
        return json_response(
            versioning.snapshot(entity_id=body.get("entity_id", ""), note=body.get("note", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edp_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        return json_response(
            ai.assist(
                action=body.get("action", "find_duplicates"),
                subject=body.get("subject", ""),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edp_analytics_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(
                {
                    "profiler": suite.profiler.status(),
                    "statistics": suite.statistics.status(),
                }
            )
        body = await _read_json(request)
        action = body.get("action", "profile")
        if action == "stats":
            return json_response(suite.statistics.summarize(), status=201)
        return json_response(suite.profiler.profile(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def edp_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = _suite().dashboard
        if request.method == "GET":
            return json_response(dashboard.status())
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "quality")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
