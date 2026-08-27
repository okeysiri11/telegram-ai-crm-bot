"""Public Vanguard career-site API — not a business vertical."""

from __future__ import annotations

import asyncio
import logging

from aiohttp import web

from applications.recruiting_enterprise.api.middleware import json_response
from services.recruiting_ops import get_recruiting_ops_service
from services.recruiting_ops.antibot import verify_antibot
from services.recruiting_ops.apply_validation import apply_timeout_seconds, max_body_bytes, validate_application_body
from services.recruiting_ops.public_limits import apply_limit, check_rate_limit, events_limit

logger = logging.getLogger(__name__)


def _client_ip(request: web.Request) -> str:
    forwarded = (request.headers.get("X-Forwarded-For") or request.headers.get("X-Real-IP") or "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()[:64] or "unknown"
    peer = request.transport.get_extra_info("peername") if request.transport else None
    return peer[0] if peer else "unknown"


def _safe_error(error: str, message_ru: str, *, extra: dict | None = None) -> dict:
    out = {"ok": False, "error": error, "message_ru": message_ru}
    if extra:
        out.update(extra)
    return out


def _status_for(result: dict, *, created: bool = False) -> int:
    if result.get("ok") is False:
        err = result.get("error")
        if err == "rate_limited":
            return 429
        if err in {"storage_unavailable", "ingest_not_configured", "anti_bot_not_configured", "anti_bot_adapter_not_wired"}:
            return 503
        if err == "payload_too_large":
            return 413
        if err == "timeout":
            return 504
        if err == "anti_bot_rejected":
            return 400
        if err == "validation":
            return 400
        return 400
    if result.get("duplicate"):
        return 200
    return 201 if created else 200


async def _read_limited_json(request: web.Request) -> tuple[dict | None, web.Response | None]:
    cl = request.content_length
    if cl is not None and cl > max_body_bytes():
        logger.info("vanguard_site payload_too_large content_length=%s ip=%s", cl, _client_ip(request))
        return None, json_response(_safe_error("payload_too_large", "Слишком большой запрос"), status=413)
    try:
        raw = await request.read()
    except Exception:
        logger.warning("vanguard_site body read failed ip=%s", _client_ip(request))
        return None, json_response(_safe_error("validation", "Некорректное тело запроса"), status=400)
    if len(raw) > max_body_bytes():
        logger.info("vanguard_site payload_too_large bytes=%s ip=%s", len(raw), _client_ip(request))
        return None, json_response(_safe_error("payload_too_large", "Слишком большой запрос"), status=413)
    if not raw:
        return {}, None
    try:
        import json as json_lib

        data = json_lib.loads(raw.decode("utf-8"))
        return (data if isinstance(data, dict) else {}), None
    except Exception:
        return None, json_response(_safe_error("validation", "Некорректный JSON"), status=400)


async def vanguard_site_apply_handler(request: web.Request) -> web.Response:
    ip = _client_ip(request)
    body, err = await _read_limited_json(request)
    if err is not None:
        return err
    assert body is not None
    validated = validate_application_body(body)
    if not validated.get("ok"):
        logger.info("vanguard_site apply validation ip=%s", ip)
        return json_response(validated, status=400)
    cleaned = validated["body"]
    ip_limit = check_rate_limit(key=f"apply:ip:{ip}", limit=apply_limit())
    if not ip_limit.get("allowed"):
        retry = int(ip_limit.get("retry_after_seconds") or 60)
        logger.info("vanguard_site apply rate_limited ip=%s", ip)
        return json_response(
            {**_safe_error("rate_limited", str(ip_limit.get("message_ru"))), "retry_after_seconds": retry},
            status=429,
            retry_after=retry,
        )
    email_limit = check_rate_limit(key=f"apply:email:{cleaned['email']}", limit=apply_limit())
    if not email_limit.get("allowed"):
        retry = int(email_limit.get("retry_after_seconds") or 60)
        logger.info("vanguard_site apply rate_limited email ip=%s", ip)
        return json_response(
            {**_safe_error("rate_limited", str(email_limit.get("message_ru"))), "retry_after_seconds": retry},
            status=429,
            retry_after=retry,
        )
    token = str(cleaned.get("antibot_token") or request.headers.get("X-Vanguard-Antibot") or "")
    antibot = verify_antibot(token=token, remote_ip=ip)
    if not antibot.get("ok"):
        logger.info("vanguard_site apply antibot error=%s ip=%s", antibot.get("error"), ip)
        status = 503 if antibot.get("error") in {"anti_bot_not_configured", "anti_bot_adapter_not_wired"} else 400
        return json_response(
            _safe_error(str(antibot.get("error") or "anti_bot_rejected"), str(antibot.get("message_ru") or "Антибот отклонён")),
            status=status,
        )
    header_key = (request.headers.get("Idempotency-Key") or "").strip()
    if header_key:
        cleaned["idempotency_key"] = header_key[:128]
    try:
        result = await asyncio.wait_for(
            get_recruiting_ops_service().submit_vanguard_application(cleaned),
            timeout=apply_timeout_seconds(),
        )
    except asyncio.TimeoutError:
        logger.error("vanguard_site apply timeout ip=%s", ip)
        return json_response(_safe_error("timeout", "Сервер не успел обработать заявку. Повторите отправку."), status=504)
    except Exception:
        logger.exception("vanguard_site apply failed ip=%s", ip)
        return json_response(_safe_error("validation", "Заявка не принята"), status=400)
    logger.info(
        "vanguard_site apply ok=%s duplicate=%s reference=%s ip=%s",
        result.get("ok"),
        result.get("duplicate"),
        result.get("reference"),
        ip,
    )
    return json_response(result, status=_status_for(result, created=not result.get("duplicate")))


async def vanguard_site_events_handler(request: web.Request) -> web.Response:
    ip = _client_ip(request)
    limited = check_rate_limit(key=f"events:ip:{ip}", limit=events_limit())
    if not limited.get("allowed"):
        retry = int(limited.get("retry_after_seconds") or 60)
        return json_response(
            {**_safe_error("rate_limited", "Слишком много событий."), "retry_after_seconds": retry},
            status=429,
            retry_after=retry,
        )
    body, err = await _read_limited_json(request)
    if err is not None:
        return err
    assert body is not None
    try:
        result = await get_recruiting_ops_service().record_vanguard_event(body)
    except Exception:
        logger.exception("vanguard_site event failed ip=%s", ip)
        return json_response(
            {"ok": False, "error": "tracking_failed", "message_ru": "Событие не доставлено", "delivery_status": "FAILED"},
            status=503,
        )
    if result.get("error") == "validation":
        return json_response(result, status=400)
    if result.get("delivery_status") == "FAILED":
        return json_response(result, status=503)
    return json_response(result, status=_status_for(result, created=not result.get("duplicate")))


async def vanguard_site_health_handler(_request: web.Request) -> web.Response:
    return json_response({"ok": True, "site": "vanguard", "path": "/vanguard", "vertical": False})


def register_vanguard_site_routes(app: web.Application) -> None:
    prefix = "/api/vanguard-site/v1"
    app.router.add_get(f"{prefix}/health", vanguard_site_health_handler)
    app.router.add_post(f"{prefix}/applications", vanguard_site_apply_handler)
    app.router.add_post(f"{prefix}/events", vanguard_site_events_handler)
