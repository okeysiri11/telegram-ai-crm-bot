"""Recruiting infrastructure diagnostics — truthful provider/store states."""

from __future__ import annotations

import os
from typing import Any

from services.recruiting_ops.projects import (
    STATUS_CONNECTED,
    STATUS_DEGRADED,
    STATUS_DISCONNECTED,
    STATUS_NOT_CONFIGURED,
    STATUS_UNKNOWN,
    vanguard_website_url,
)
from services.recruiting_ops.provider_readiness import ads_readiness, antibot_readiness, messaging_readiness
from services.recruiting_ops.runtime import is_production_runtime
from services.recruiting_ops.shared_store import get_store, redis_reachable
from services.recruiting_ops.tracking_health import build_tracking_diagnostics
from services.recruiting_ops.tracking_worker import get_tracking_worker

CHIP = {
    STATUS_CONNECTED: ("Работает", "success"),
    STATUS_NOT_CONFIGURED: ("Не настроено", "info"),
    "CONFIGURED": ("Ограничено", "warning"),
    STATUS_DEGRADED: ("Ограничено", "warning"),
    "ERROR": ("Ошибка", "danger"),
    STATUS_DISCONNECTED: ("Ошибка", "danger"),
    STATUS_UNKNOWN: ("Не настроено", "info"),
}


def chip(code: str, *, reason_ru: str | None = None) -> dict[str, Any]:
    label, tone = CHIP.get(code, ("Ограничено", "warning"))
    if code == STATUS_NOT_CONFIGURED:
        label, tone = "Не настроено", "info"
    out: dict[str, Any] = {
        "code": code,
        "label_ru": label,
        "tone": tone,
        "status_label_ru": label,
    }
    if reason_ru:
        out["reason_ru"] = reason_ru
    return out


def _store_chip(desc: dict[str, Any]) -> dict[str, Any]:
    backend = desc.get("backend")
    if backend == "redis" and desc.get("shared"):
        return chip(STATUS_CONNECTED, reason_ru="Redis, общий между процессами.")
    if backend == "unavailable" or desc.get("fail_closed"):
        return chip("ERROR", reason_ru=str(desc.get("reason") or "Хранилище недоступно."))
    if backend == "process_local":
        return chip(
            STATUS_DEGRADED,
            reason_ru="process_local — не общее хранилище. SHARED=NO.",
        )
    return chip(STATUS_DEGRADED, reason_ru=str(desc.get("reason") or backend))


def _ci_e2e_chip() -> dict[str, Any]:
    raw = (os.getenv("VANGUARD_CI_E2E_STATUS") or "").strip().upper()
    if raw == "PASS":
        return chip(STATUS_CONNECTED, reason_ru="CI Playwright PASS (из VANGUARD_CI_E2E_STATUS).")
    if raw == "FAIL":
        return chip("ERROR", reason_ru="CI Playwright FAIL (из VANGUARD_CI_E2E_STATUS).")
    if raw == "BLOCKED":
        return chip(STATUS_DEGRADED, reason_ru="CI Playwright BLOCKED (из VANGUARD_CI_E2E_STATUS).")
    return chip(
        STATUS_NOT_CONFIGURED,
        reason_ru="Статус CI E2E не передан в этот процесс (VANGUARD_CI_E2E_STATUS).",
    )


async def build_ops_diagnostics(service: Any) -> dict[str, Any]:
    recovery = await service.recover_tracking_records()
    db_code, db_reason = await service._storage_probe_reason()
    store = get_store().describe()
    redis_ok = redis_reachable()
    if redis_ok:
        redis_chip = chip(STATUS_CONNECTED, reason_ru="REDIS_URL отвечает PING.")
    elif (os.getenv("REDIS_URL") or os.getenv("VANGUARD_SHARED_STORE_URL") or "").strip():
        redis_chip = chip(
            STATUS_DEGRADED if not is_production_runtime() else "ERROR",
            reason_ru="REDIS_URL задан, но Redis недоступен.",
        )
    else:
        redis_chip = chip(STATUS_NOT_CONFIGURED, reason_ru="REDIS_URL не задан.")

    org = str(os.getenv("VANGUARD_ORGANIZATION_ID") or "ados")
    await service.ensure_hydrated(org)
    events = service._bag(org).get("tracking") or []
    tracking = build_tracking_diagnostics(events)
    tracking_chip = chip(tracking["code"], reason_ru=tracking.get("reason_ru"))

    url = vanguard_website_url()
    if url:
        website = chip(STATUS_CONNECTED, reason_ru=f"VANGUARD_WEBSITE_URL={url}")
        website["url"] = url
    else:
        website = chip(
            STATUS_NOT_CONFIGURED,
            reason_ru="Требуется VANGUARD_WEBSITE_URL (канонический публичный URL). Не выдуман.",
        )
        website["required_env"] = ["VANGUARD_WEBSITE_URL"]
        website["documented_example"] = "https://ados-web.onrender.com/vanguard"

    from services.recruiting_ops.ingest_auth import resolve_ingest_secret

    if resolve_ingest_secret() and db_code == STATUS_CONNECTED:
        integ_chip = chip(STATUS_CONNECTED, reason_ru="HMAC ingest и PostgreSQL доступны.")
    elif not resolve_ingest_secret() and is_production_runtime():
        integ_chip = chip(STATUS_DISCONNECTED, reason_ru="VANGUARD_INGEST_SECRET не задан в production.")
    elif db_code != STATUS_CONNECTED:
        integ_chip = chip(db_code, reason_ru=db_reason)
    else:
        integ_chip = chip(STATUS_DEGRADED, reason_ru="DEV fallback ingest secret.")

    ads = ads_readiness()["providers"]
    msg = messaging_readiness()["channels"]
    anti = antibot_readiness()

    components = {
        "postgresql": chip(db_code, reason_ru=db_reason),
        "redis": redis_chip,
        "rate_limit_store": {**_store_chip(store), "backend": store.get("backend"), "shared": store.get("shared")},
        "replay_store": {**_store_chip(store), "backend": store.get("backend"), "shared": store.get("shared")},
        "tracking_worker": chip(
            STATUS_CONNECTED if get_tracking_worker().enabled else "ERROR",
            reason_ru="Воркер трекинга в процессе API.",
        ),
        "vanguard_integration": integ_chip,
        "vanguard_website": website,
        "meta_ads": chip(ads["meta"]["status"], reason_ru=ads["meta"]["message_ru"]),
        "google_ads": chip(ads["google"]["status"], reason_ru=ads["google"]["message_ru"]),
        "tiktok_ads": chip(ads["tiktok"]["status"], reason_ru=ads["tiktok"]["message_ru"]),
        "telegram": chip(msg["telegram"]["status"], reason_ru=msg["telegram"]["message_ru"]),
        "whatsapp": chip(msg["whatsapp"]["status"], reason_ru=msg["whatsapp"]["message_ru"]),
        "email": chip(msg["email"]["status"], reason_ru=msg["email"]["message_ru"]),
        "anti_bot": chip(anti["status"], reason_ru=anti["message_ru"]),
        "ci_e2e": _ci_e2e_chip(),
    }
    for key, spec in (("meta_ads", ads["meta"]), ("google_ads", ads["google"]), ("tiktok_ads", ads["tiktok"])):
        components[key]["missing"] = spec.get("missing") or []
        components[key]["connected"] = False
    components["anti_bot"]["captcha_active"] = False
    components["anti_bot"]["missing"] = anti.get("missing") or []
    components["tracking_worker"]["snapshot"] = get_tracking_worker().snapshot()

    return {
        "ok": True,
        "sprint": "recruiting_1.6",
        "components": components,
        "tracking": tracking,
        "tracking_recovery": recovery,
        "store": store,
        "ads": ads,
        "messaging": msg,
        "antibot": anti,
        "website_required_env": "VANGUARD_WEBSITE_URL",
        "fake_pass": False,
    }
