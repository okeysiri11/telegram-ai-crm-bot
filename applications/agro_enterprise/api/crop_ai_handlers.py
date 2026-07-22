"""API handlers — Crop AI (Sprint 14.3)."""

from __future__ import annotations

from aiohttp import web

from applications.agro_enterprise import agro_enterprise
from applications.agro_enterprise.api.middleware import json_response
from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return agro_enterprise.crop_ai


async def ca_health_handler(request: web.Request) -> web.Response:
    health = agro_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "crop_ai_ready": health.get("crop_ai_ready"),
            "disease_detection_ready": health.get("disease_detection_ready"),
            "pest_intelligence_ready": health.get("pest_intelligence_ready"),
            "yield_intelligence_ready": health.get("yield_intelligence_ready"),
            "autonomous_farm_ready": health.get("autonomous_farm_ready"),
            "suite": _suite().status(),
        }
    )


async def ca_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ca_crops_handler(request: web.Request) -> web.Response:
    try:
        crops = _suite().crops
        if request.method == "GET":
            cid = request.rel_url.query.get("crop_id")
            if cid:
                return json_response(crops.analytics(cid))
            return json_response(crops.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "stage":
            return json_response(
                crops.track_stage(
                    body.get("crop_id", ""),
                    stage=body.get("stage", "vegetative"),
                    phenology_day=int(body.get("phenology_day", 0) or 0),
                ),
                status=201,
            )
        if action == "health":
            return json_response(
                crops.health(body.get("crop_id", ""), health_score=float(body.get("health_score", 80) or 80)),
                status=201,
            )
        if action == "readiness":
            return json_response(crops.harvest_readiness(body.get("crop_id", "")), status=201)
        return json_response(
            crops.register_crop(
                name=body.get("name", ""),
                variety=body.get("variety", ""),
                field_id=body.get("field_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ca_disease_handler(request: web.Request) -> web.Response:
    try:
        disease = _suite().disease
        if request.method == "GET":
            return json_response(disease.status())
        body = await _read_json(request)
        return json_response(
            disease.detect(
                crop_id=body.get("crop_id", ""),
                part=body.get("part", "leaf"),
                disease_type=body.get("disease_type", "fungal"),
                confidence=float(body.get("confidence", 0.8) or 0.8),
                severity=float(body.get("severity", 0.3) or 0.3),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ca_pest_handler(request: web.Request) -> web.Response:
    try:
        pests = _suite().pests
        if request.method == "GET":
            return json_response(pests.status())
        body = await _read_json(request)
        action = body.get("action", "identify")
        if action == "risk_map":
            return json_response(pests.risk_map(region=body.get("region", "")), status=201)
        return json_response(
            pests.identify(
                crop_id=body.get("crop_id", ""),
                pest_name=body.get("pest_name", ""),
                population_index=float(body.get("population_index", 0.4) or 0.4),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ca_yield_handler(request: web.Request) -> web.Response:
    try:
        yield_intel = _suite().yield_intel
        if request.method == "GET":
            cid = request.rel_url.query.get("crop_id", "")
            if cid or request.rel_url.query.get("history"):
                return json_response({"history": yield_intel.history(cid)})
            return json_response(yield_intel.status())
        body = await _read_json(request)
        return json_response(
            yield_intel.predict(
                crop_id=body.get("crop_id", ""),
                hectares=float(body.get("hectares", 10) or 10),
                health_score=float(body.get("health_score", 80) or 80),
                ndvi=float(body.get("ndvi", 0.6) or 0.6),
                region=body.get("region", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ca_ops_handler(request: web.Request) -> web.Response:
    try:
        ops = _suite().ops
        if request.method == "GET":
            return json_response(ops.status())
        body = await _read_json(request)
        action = body.get("action", "task")
        if action == "mission":
            return json_response(
                ops.schedule_mission(
                    field_id=body.get("field_id", ""),
                    mission_type=body.get("mission_type", "scout"),
                    assignee=body.get("assignee", "drone"),
                    starts_at=body.get("starts_at", ""),
                ),
                status=201,
            )
        if action == "assign":
            return json_response(
                ops.assign(
                    body.get("mission_id", ""),
                    asset=body.get("asset", ""),
                    asset_kind=body.get("asset_kind", "drone"),
                ),
                status=201,
            )
        return json_response(
            ops.plan_task(
                field_id=body.get("field_id", ""),
                title=body.get("title", ""),
                task_type=body.get("task_type", "scout"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ca_decisions_handler(request: web.Request) -> web.Response:
    try:
        decisions = _suite().decisions
        if request.method == "GET":
            return json_response(decisions.status())
        body = await _read_json(request)
        return json_response(
            decisions.recommend(
                crop_id=body.get("crop_id", ""),
                intent=body.get("intent", "treatment"),
                context=body.get("context"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ca_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            return json_response(dash.render(dashboard_type=request.rel_url.query.get("type", "crop_health")))
        body = await _read_json(request)
        return json_response(dash.render(dashboard_type=body.get("dashboard_type", "crop_health")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ca_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "crop"),
                key=body.get("key", ""),
                payload=body.get("payload"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
