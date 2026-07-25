"""API handlers — Performance Testing (Sprint 25.2)."""

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
    return enterprise_hub.performance_testing


async def epl_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "performance_testing_ready": health.get("performance_testing_ready"),
            "load_testing_ready": health.get("load_testing_ready"),
            "stress_testing_ready": health.get("stress_testing_ready"),
            "bottleneck_advisor_ready": health.get("bottleneck_advisor_ready"),
            "suite": _suite().status(),
        }
    )


async def epl_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def epl_load_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().load_test(users=int(body.get("users", 100))), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def epl_stress_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().stress_test(
                start_users=int(body.get("start_users", 100)),
                step=int(body.get("step", 200)),
                max_users=int(body.get("max_users", 5000)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epl_spike_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().spike_test(pattern=body.get("pattern")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def epl_soak_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().soak_test(hours=int(body.get("hours", 1)), users=int(body.get("users", 100))),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epl_bench_api_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().benchmark_api(endpoint=body.get("endpoint", "/"), samples=body.get("samples")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epl_bench_db_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().benchmark_database(
                reads_ms=float(body.get("reads_ms", 12)),
                writes_ms=float(body.get("writes_ms", 18)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epl_bench_ai_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().benchmark_ai(
                latency_ms=float(body.get("latency_ms", 350)),
                tokens=int(body.get("tokens", 800)),
                cost=float(body.get("cost", 0.02)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epl_bench_wf_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().benchmark_workflow(
                steps=int(body.get("steps", 5)),
                duration_ms=float(body.get("duration_ms", 900)),
                parallel=int(body.get("parallel", 2)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epl_monitor_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().monitor(load_users=int(body.get("load_users", 0))), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def epl_analyze_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().analyze(
                load_users=int(body.get("load_users", 500)),
                endpoint=body.get("endpoint", "/api/enterprise-hub/v1/health"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epl_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)
