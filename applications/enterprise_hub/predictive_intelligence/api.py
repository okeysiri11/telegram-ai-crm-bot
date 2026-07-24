"""API handlers — Predictive Intelligence (Sprint 24.3)."""

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
    return enterprise_hub.predictive_intelligence


async def pin_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "predictive_intelligence_ready": health.get("predictive_intelligence_ready"),
            "business_forecast_ready": health.get("business_forecast_ready"),
            "risk_intelligence_ready": health.get("risk_intelligence_ready"),
            "opportunity_detector_ready": health.get("opportunity_detector_ready"),
            "suite": _suite().status(),
        }
    )


async def pin_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def pin_models_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response(_suite().list_models())
        body = await _read_json(request)
        return json_response(
            _suite().register_model(
                model_id=body.get("model_id", ""),
                domain=body.get("domain", ""),
                prediction_type=body.get("prediction_type", ""),
                data_sources=body.get("data_sources"),
                accuracy=float(body.get("accuracy", 0.8)),
                status=body.get("status", "active"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pin_business_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().business_forecast(
                domain=body.get("domain", "revenue"),
                horizon_days=int(body.get("horizon_days", 30)),
                baseline=float(body.get("baseline", 100.0)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pin_customer_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().customer_predict(customer_id=body.get("customer_id", ""), signals=body.get("signals")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pin_marketing_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().marketing_predict(
                campaign_id=body.get("campaign_id", ""),
                channel=body.get("channel", "push"),
                budget=float(body.get("budget", 100)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pin_operations_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().operations_predict(
                branch_id=body.get("branch_id", ""),
                load_pct=float(body.get("load_pct", 0.7)),
                inventory_days=float(body.get("inventory_days", 10)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pin_risk_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().assess_risks(signals=body.get("signals")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def pin_opportunity_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().detect_opportunities(signals=body.get("signals")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def pin_learn_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().learn(
                forecast=float(body.get("forecast", 0)),
                actual=float(body.get("actual", 0)),
                confirmed=bool(body.get("confirmed", False)),
                model_id=body.get("model_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pin_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().owner_dashboard())
    except Exception as exc:
        return _handle_error(exc)
