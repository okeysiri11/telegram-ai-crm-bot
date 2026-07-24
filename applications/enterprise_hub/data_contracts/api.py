"""API handlers — Enterprise Data Contracts (Sprint 21.3)."""

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
    return enterprise_hub.data_contracts


async def edc_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "data_contracts_ready": health.get("data_contracts_ready"),
            "dto_registry_ready": health.get("dto_registry_ready"),
            "schema_registry_ready": health.get("schema_registry_ready"),
            "contract_testing_ready": health.get("contract_testing_ready"),
            "suite": _suite().status(),
        }
    )


async def edc_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def edc_dtos_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            items = suite.store.edc_dto_registry.list_all() or suite.library.dto_registry.list_all()
            return json_response({"dtos": len(items), "items": items})
        body = await _read_json(request)
        created = suite.register_dto(
            name=body.get("name", ""),
            domain=body.get("domain", "common"),
            fields=body.get("fields") if isinstance(body.get("fields"), list) else None,
        )
        return json_response(created, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def edc_schemas_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            name = request.rel_url.query.get("name", "BaseDTO")
            version = request.rel_url.query.get("version")
            ver = int(version) if version else None
            return json_response(suite.get_schema(name, ver))
        body = await _read_json(request)
        created = suite.publish_schema(
            name=body.get("name", ""),
            schema=body.get("schema") if isinstance(body.get("schema"), dict) else {},
            version=int(body["version"]) if body.get("version") is not None else None,
        )
        return json_response(created, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def edc_validate_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().validate_dto(body.get("dto") if isinstance(body.get("dto"), dict) else body), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def edc_serialize_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().serialize(
                body.get("data") if isinstance(body.get("data"), dict) else body,
                format=body.get("format", "json"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edc_map_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().map_dto_to_event(body.get("dto") if isinstance(body.get("dto"), dict) else body),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edc_tests_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().run_contract_tests(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def edc_docs_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().documentation())
    except Exception as exc:
        return _handle_error(exc)
