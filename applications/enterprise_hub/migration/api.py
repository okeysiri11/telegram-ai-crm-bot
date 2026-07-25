"""API handlers — Migration & DR (Sprint 25.4)."""

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
    return enterprise_hub.migration


async def emr_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "migration_platform_ready": health.get("migration_platform_ready"),
            "backup_manager_ready": health.get("backup_manager_ready"),
            "rollback_ready": health.get("rollback_ready"),
            "disaster_recovery_ready": health.get("disaster_recovery_ready"),
            "suite": _suite().status(),
        }
    )


async def emr_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def emr_migration_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().create_migration(
                migration_id=body.get("migration_id") or f"mig_{uuid.uuid4().hex[:8]}",
                version_from=body.get("version_from", ""),
                version_to=body.get("version_to", ""),
                module=body.get("module", ""),
                author=body.get("author", "system"),
                dependencies=body.get("dependencies"),
                rollback_support=bool(body.get("rollback_support", True)),
                validation_rules=body.get("validation_rules"),
                status=body.get("status", "pending"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def emr_migrations_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().list_migrations())
    except Exception as exc:
        return _handle_error(exc)


async def emr_run_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().run_migration(
                migration_id=body.get("migration_id", ""),
                schema_ops=body.get("schema_ops"),
                data_ops=body.get("data_ops"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def emr_backup_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().backup(kind=body.get("kind"), label=body.get("label", "manual")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def emr_restore_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().restore(target=body.get("target", ""), backup_id=body.get("backup_id", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def emr_rollback_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().rollback(
                mode=body.get("mode", "last"),
                migration_id=body.get("migration_id", ""),
                version=body.get("version", ""),
                migration_ids=body.get("migration_ids"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def emr_validate_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().validate_recovery(fail_check=body.get("fail_check")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def emr_disaster_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().disaster_test(
                scenario=body.get("scenario"),
                all_scenarios=bool(body.get("all_scenarios", False)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def emr_versions_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().version_status())
    except Exception as exc:
        return _handle_error(exc)


async def emr_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)
