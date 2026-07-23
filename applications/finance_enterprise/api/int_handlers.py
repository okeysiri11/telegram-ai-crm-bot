"""API handlers — Enterprise Financial Integration (Sprint 18.7)."""

from __future__ import annotations

from aiohttp import web

from applications.finance_enterprise import finance_enterprise
from applications.finance_enterprise.api.middleware import json_response
from applications.finance_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return finance_enterprise.integration


async def int_health_handler(request: web.Request) -> web.Response:
    health = finance_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "enterprise_financial_integration_ready": health.get(
                "enterprise_financial_integration_ready"
            ),
            "cross_platform_operations_ready": health.get("cross_platform_operations_ready"),
            "financial_event_bus_ready": health.get("financial_event_bus_ready"),
            "ai_enterprise_finance_ready": health.get("ai_enterprise_finance_ready"),
            "suite": _suite().status(),
        }
    )


async def int_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def int_events_handler(request: web.Request) -> web.Response:
    try:
        bus = _suite().event_bus
        if request.method == "GET":
            return json_response(bus.status())
        body = await _read_json(request)
        action = body.get("action", "publish")
        if action == "register":
            return json_response(
                bus.register_event_type(
                    name=body.get("name", ""),
                    platform=body.get("platform", ""),
                    schema=body.get("schema", ""),
                ),
                status=201,
            )
        if action == "replay":
            return json_response(bus.replay(event_id=body.get("event_id", "")), status=201)
        if action == "monitor":
            return json_response(bus.monitor(), status=201)
        return json_response(
            bus.publish(
                platform=body.get("platform", ""),
                event_kind=body.get("event_kind", "transaction"),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
                amount=float(body.get("amount", 0) or 0),
                reference=body.get("reference", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


def _platform_adapter(name: str):
    suite = _suite()
    return {
        "automotive": suite.automotive,
        "agro": suite.agro,
        "port": suite.port,
        "crypto": suite.crypto,
        "legal": suite.legal,
    }.get(name)


async def int_platforms_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response(
                {
                    "automotive": _suite().automotive.status(),
                    "agro": _suite().agro.status(),
                    "port": _suite().port.status(),
                    "crypto": _suite().crypto.status(),
                    "legal": _suite().legal.status(),
                }
            )
        body = await _read_json(request)
        platform = body.get("platform", "automotive").lower()
        adapter = _platform_adapter(platform)
        if adapter is None:
            raise ValidationError("platform must be automotive|agro|port|crypto|legal")
        return json_response(
            adapter.operate(
                operation=body.get("operation", ""),
                amount=float(body.get("amount", 0) or 0),
                reference=body.get("reference", ""),
                detail=body.get("detail", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def int_intelligence_handler(request: web.Request) -> web.Response:
    try:
        intelligence = _suite().intelligence
        if request.method == "GET":
            return json_response(intelligence.status())
        body = await _read_json(request)
        action = body.get("action", "analyze")
        if action == "dependency":
            return json_response(
                intelligence.map_dependency(
                    from_platform=body.get("from_platform", ""),
                    to_platform=body.get("to_platform", ""),
                    dependency=body.get("dependency", ""),
                    strength=float(body.get("strength", 0.5) or 0.5),
                ),
                status=201,
            )
        return json_response(
            intelligence.analyze(
                analytic_type=body.get("analytic_type", "enterprise_revenue"),
                subject=body.get("subject", ""),
                value=float(body.get("value", 0) or 0),
                platforms=body.get("platforms") if isinstance(body.get("platforms"), list) else None,
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def int_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "insight")
        if action == "nl_report":
            return json_response(ai.nl_report(audience=body.get("audience", "executive")), status=201)
        if action == "health_score":
            return json_response(
                ai.health_score(
                    subject=body.get("subject", "enterprise"),
                    score=float(body.get("score", 0.86) or 0.86),
                ),
                status=201,
            )
        return json_response(
            ai.insight(
                insight_type=body.get("insight_type", "process_monitoring"),
                subject=body.get("subject", ""),
                score=float(body.get("score", 0.7) or 0.7),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def int_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("dashboard_type", "enterprise_finance")
            return json_response(dashboard.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "enterprise_finance")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def int_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                base=body.get("base", "integration"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
