"""API handlers — Test Infrastructure (Sprint 25.1)."""

from __future__ import annotations

import uuid

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
    return enterprise_hub.test_infrastructure


async def eti_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "test_infrastructure_ready": health.get("test_infrastructure_ready"),
            "test_registry_ready": health.get("test_registry_ready"),
            "test_runner_ready": health.get("test_runner_ready"),
            "test_dashboard_ready": health.get("test_dashboard_ready"),
            "suite": _suite().status(),
        }
    )


async def eti_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eti_register_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().register_test(
                test_id=body.get("test_id") or f"tst_{uuid.uuid4().hex[:8]}",
                name=body.get("name", ""),
                module=body.get("module", ""),
                category=body.get("category", "unit"),
                priority=body.get("priority", "medium"),
                owner=body.get("owner", "qa"),
                dependencies=body.get("dependencies"),
                tags=body.get("tags"),
                estimated_duration_ms=int(body.get("estimated_duration_ms", 100)),
                version=body.get("version", "1.0"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eti_tests_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().list_tests())
    except Exception as exc:
        return _handle_error(exc)


async def eti_run_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().run(
                test_id=body.get("test_id"),
                group=body.get("group"),
                module=body.get("module"),
                tag=body.get("tag"),
                changed_files=body.get("changed_files"),
                full=bool(body.get("full", False)),
                environment=body.get("environment", "ci"),
                fail_ids=body.get("fail_ids"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eti_smoke_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().smoke(modules=body.get("modules")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eti_integration_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().integration_check(pairs=body.get("pairs")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eti_regression_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().regression(
                baseline_pass_rate=float(body.get("baseline_pass_rate", 1.0)),
                current_pass_rate=float(body.get("current_pass_rate", 1.0)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eti_contracts_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().validate_contracts(contracts=body.get("contracts")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eti_coverage_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().coverage(
                covered_lines=int(body.get("covered_lines", 0)),
                total_lines=int(body.get("total_lines", 1)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eti_data_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().generate_data(entity=body.get("entity", ""), count=int(body.get("count", 1))),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eti_env_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().provision_env(environment=body.get("environment", "local")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eti_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def eti_analytics_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().analytics())
    except Exception as exc:
        return _handle_error(exc)
