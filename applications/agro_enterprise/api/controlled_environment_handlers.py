"""API handlers — Controlled Environment (Sprint 14.4)."""

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
    return agro_enterprise.controlled_environment


async def ce_health_handler(request: web.Request) -> web.Response:
    health = agro_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "smart_greenhouse_ready": health.get("smart_greenhouse_ready"),
            "livestock_platform_ready": health.get("livestock_platform_ready"),
            "poultry_platform_ready": health.get("poultry_platform_ready"),
            "aquaculture_platform_ready": health.get("aquaculture_platform_ready"),
            "controlled_environment_agriculture_ready": health.get(
                "controlled_environment_agriculture_ready"
            ),
            "suite": _suite().status(),
        }
    )


async def ce_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ce_greenhouse_handler(request: web.Request) -> web.Response:
    try:
        gh = _suite().greenhouse
        if request.method == "GET":
            return json_response(gh.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "zone":
            return json_response(
                gh.create_zone(
                    greenhouse_id=body.get("greenhouse_id", ""),
                    name=body.get("name", "Zone"),
                ),
                status=201,
            )
        if action == "climate":
            return json_response(
                gh.set_climate(
                    body.get("zone_id", ""),
                    temp_c=body.get("temp_c"),
                    humidity_pct=body.get("humidity_pct"),
                    co2_ppm=body.get("co2_ppm"),
                ),
                status=201,
            )
        if action == "control":
            return json_response(
                gh.control(
                    body.get("zone_id", ""),
                    control=body.get("control", "lighting"),
                    enabled=bool(body.get("enabled", True)),
                    setpoint=body.get("setpoint"),
                ),
                status=201,
            )
        if action == "schedule":
            return json_response(
                gh.schedule_crop(
                    zone_id=body.get("zone_id", ""),
                    crop=body.get("crop", ""),
                    starts_at=body.get("starts_at", ""),
                    ends_at=body.get("ends_at", ""),
                ),
                status=201,
            )
        if action == "yield":
            return json_response(
                gh.record_yield(zone_id=body.get("zone_id", ""), kg=float(body.get("kg", 0) or 0)),
                status=201,
            )
        return json_response(
            gh.register_greenhouse(
                name=body.get("name", ""),
                area_m2=float(body.get("area_m2", 1000) or 1000),
                location=body.get("location", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ce_climate_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().climate_ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        return json_response(
            ai.optimize(
                zone_id=body.get("zone_id", ""),
                temp_c=float(body.get("temp_c", 24) or 24),
                humidity_pct=float(body.get("humidity_pct", 60) or 60),
                energy_cost=float(body.get("energy_cost", 0.2) or 0.2),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ce_livestock_handler(request: web.Request) -> web.Response:
    try:
        ls = _suite().livestock
        if request.method == "GET":
            return json_response(ls.status())
        body = await _read_json(request)
        action = body.get("action", "register_animal")
        if action == "breed":
            return json_response(
                ls.register_breed(name=body.get("name", ""), species=body.get("species", "cattle")),
                status=201,
            )
        if action == "health":
            return json_response(
                ls.health(
                    body.get("animal_id", ""),
                    health_score=float(body.get("health_score", 90) or 90),
                    note=body.get("note", ""),
                ),
                status=201,
            )
        if action == "vaccinate":
            return json_response(
                ls.vaccinate(body.get("animal_id", ""), vaccine=body.get("vaccine", "")),
                status=201,
            )
        if action == "feed":
            return json_response(
                ls.feed(body.get("animal_id", ""), ration_kg=float(body.get("ration_kg", 0) or 0)),
                status=201,
            )
        if action == "weigh":
            return json_response(
                ls.weigh(body.get("animal_id", ""), weight_kg=float(body.get("weight_kg", 0) or 0)),
                status=201,
            )
        if action == "milk":
            return json_response(
                ls.milk(body.get("animal_id", ""), liters=float(body.get("liters", 0) or 0)),
                status=201,
            )
        if action == "reproduction":
            return json_response(
                ls.reproduction(body.get("animal_id", ""), status=body.get("status", "pregnant")),
                status=201,
            )
        return json_response(
            ls.register_animal(
                tag=body.get("tag", ""),
                breed_id=body.get("breed_id", ""),
                sex=body.get("sex", "F"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ce_poultry_handler(request: web.Request) -> web.Response:
    try:
        poultry = _suite().poultry
        if request.method == "GET":
            return json_response(poultry.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "eggs":
            return json_response(
                poultry.record_eggs(body.get("flock_id", ""), count=int(body.get("count", 0) or 0)),
                status=201,
            )
        if action == "mortality":
            return json_response(
                poultry.mortality(
                    body.get("flock_id", ""),
                    count=int(body.get("count", 0) or 0),
                    reason=body.get("reason", ""),
                ),
                status=201,
            )
        return json_response(
            poultry.register_flock(name=body.get("name", ""), birds=int(body.get("birds", 1000) or 1000)),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ce_aquaculture_handler(request: web.Request) -> web.Response:
    try:
        aqua = _suite().aquaculture
        if request.method == "GET":
            return json_response(aqua.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "water":
            return json_response(
                aqua.water_quality(
                    body.get("farm_id", ""),
                    oxygen_mg_l=float(body.get("oxygen_mg_l", 6) or 6),
                    temp_c=float(body.get("temp_c", 26) or 26),
                    ph=float(body.get("ph", 7) or 7),
                ),
                status=201,
            )
        if action == "feed":
            return json_response(
                aqua.feed(body.get("farm_id", ""), kg=float(body.get("kg", 0) or 0)),
                status=201,
            )
        if action == "growth":
            return json_response(
                aqua.growth_prediction(
                    body.get("farm_id", ""),
                    biomass_kg=float(body.get("biomass_kg", 0) or 0),
                    days=int(body.get("days", 30) or 30),
                ),
                status=201,
            )
        return json_response(
            aqua.register_farm(name=body.get("name", ""), species=body.get("species", "tilapia")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ce_biosecurity_handler(request: web.Request) -> web.Response:
    try:
        bio = _suite().biosecurity
        if request.method == "GET":
            return json_response(bio.status())
        body = await _read_json(request)
        action = body.get("action", "incident")
        if action == "access":
            return json_response(
                bio.access(
                    site=body.get("site", ""),
                    principal=body.get("principal", ""),
                    granted=bool(body.get("granted", True)),
                ),
                status=201,
            )
        if action == "quarantine":
            return json_response(
                bio.quarantine(subject=body.get("subject", ""), reason=body.get("reason", "")),
                status=201,
            )
        if action == "sanitation":
            return json_response(
                bio.sanitation(area=body.get("area", ""), status=body.get("status", "completed")),
                status=201,
            )
        if action == "compliance":
            return json_response(
                bio.compliance(framework=body.get("framework", ""), status=body.get("status", "compliant")),
                status=201,
            )
        return json_response(
            bio.incident(title=body.get("title", ""), severity=body.get("severity", "medium")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ce_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "greenhouse")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "greenhouse")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ce_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "greenhouse"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
