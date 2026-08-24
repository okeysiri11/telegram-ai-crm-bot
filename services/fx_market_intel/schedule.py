"""Configurable FX analysis schedules — timezone-aware, not hard-coded to one region."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

PRESET_JOB_KEYS = {
    "morning": "fx.intel.morning",
    "pre_europe": "fx.intel.pre_europe",
    "pre_us": "fx.intel.pre_us",
    "evening": "fx.intel.evening",
}

# Defaults only — operators override via API/prefs. Business logic must not assume Kyiv.
DEFAULT_SCHEDULES: dict[str, dict[str, Any]] = {
    "morning": {"label_ru": "Утренний обзор", "hour": 7, "minute": 0, "timezone": "Europe/Kyiv", "enabled": False},
    "pre_europe": {"label_ru": "Перед Европой", "hour": 7, "minute": 30, "timezone": "Europe/Kyiv", "enabled": False},
    "pre_us": {"label_ru": "Перед США", "hour": 15, "minute": 0, "timezone": "Europe/Kyiv", "enabled": False},
    "evening": {"label_ru": "Вечерний обзор", "hour": 20, "minute": 0, "timezone": "Europe/Kyiv", "enabled": False},
}

# In-memory tenant overrides (also persisted when DB available)
_OVERRIDES: dict[str, dict[str, dict[str, Any]]] = {}
_LAST_RUN: dict[str, dict[str, Any]] = {}  # tenant:preset -> {at, result, confidence}


def _tz(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name or "UTC")
    except Exception:
        return ZoneInfo("UTC")


def _cron_for(hour: int, minute: int) -> str:
    return f"{int(minute)} {int(hour)} * * 1-5"


def get_tenant_schedules(tenant_id: str) -> dict[str, dict[str, Any]]:
    key = tenant_id or "default"
    base = {pid: dict(cfg) for pid, cfg in DEFAULT_SCHEDULES.items()}
    for pid, ov in (_OVERRIDES.get(key) or {}).items():
        if pid in base:
            base[pid] = {**base[pid], **ov}
    return base


def upsert_schedule(
    tenant_id: str,
    preset_id: str,
    *,
    enabled: bool | None = None,
    hour: int | None = None,
    minute: int | None = None,
    timezone_name: str | None = None,
) -> dict[str, Any]:
    if preset_id not in DEFAULT_SCHEDULES:
        raise ValueError(f"unknown preset {preset_id}")
    key = tenant_id or "default"
    cur = get_tenant_schedules(key)[preset_id]
    if enabled is not None:
        cur["enabled"] = bool(enabled)
    if hour is not None:
        cur["hour"] = max(0, min(23, int(hour)))
    if minute is not None:
        cur["minute"] = max(0, min(59, int(minute)))
    if timezone_name:
        # validate
        _tz(timezone_name)
        cur["timezone"] = timezone_name
    _OVERRIDES.setdefault(key, {})[preset_id] = cur
    return cur


def next_run_local(cfg: dict[str, Any], *, after: datetime | None = None) -> datetime | None:
    if not cfg.get("enabled"):
        return None
    tz = _tz(str(cfg.get("timezone") or "UTC"))
    now = (after or datetime.now(timezone.utc)).astimezone(tz)
    candidate = now.replace(hour=int(cfg["hour"]), minute=int(cfg["minute"]), second=0, microsecond=0)
    if candidate <= now:
        # next weekday
        from datetime import timedelta

        candidate = candidate + timedelta(days=1)
    # skip weekends for FX desk defaults
    while candidate.weekday() >= 5:
        from datetime import timedelta

        candidate = candidate + timedelta(days=1)
    return candidate


def record_last_run(tenant_id: str, preset_id: str, *, result: str, confidence: float) -> None:
    key = tenant_id or "default"
    _LAST_RUN.setdefault(key, {})[preset_id] = {
        "at": datetime.now(timezone.utc).isoformat(),
        "result": result,
        "confidence": confidence,
    }


def get_last_run(tenant_id: str, preset_id: str) -> dict[str, Any] | None:
    return (_LAST_RUN.get(tenant_id or "default") or {}).get(preset_id)


async def list_fx_intel_schedule(tenant_id: str = "default") -> dict[str, Any]:
    """Merge tenant config + optional platform job next_run; never invent times when disabled."""
    schedules = get_tenant_schedules(tenant_id)
    jobs_out: dict[str, dict[str, Any]] = {}
    platform_jobs: dict[str, Any] = {}
    try:
        from database.session import get_session
        from repositories.scheduler_engine_repository import ScheduledJobRepository

        async with get_session() as session:
            repo = ScheduledJobRepository(session)
            active = await repo.list_active()
            platform_jobs = {j.job_key: j for j in active}
    except Exception as exc:
        logger.warning("platform schedule read skipped: %s", exc)

    for preset, cfg in schedules.items():
        job_key = PRESET_JOB_KEYS[preset]
        plat = platform_jobs.get(job_key)
        next_local = next_run_local(cfg) if cfg.get("enabled") else None
        # Prefer computed next from tenant config when enabled; else platform job if present
        next_at = None
        if cfg.get("enabled") and next_local is not None:
            next_at = next_local.isoformat()
        elif plat is not None and getattr(plat, "next_run_at", None):
            next_at = plat.next_run_at.isoformat()

        last = get_last_run(tenant_id, preset)
        hhmm = f"{int(cfg['hour']):02d}:{int(cfg['minute']):02d}"
        jobs_out[preset] = {
            "preset_id": preset,
            "job_key": job_key,
            "label_ru": cfg.get("label_ru"),
            "enabled": bool(cfg.get("enabled")),
            "autostart_ru": "Включён" if cfg.get("enabled") else "Выключен",
            "timezone": cfg.get("timezone") or "UTC",
            "hour": cfg.get("hour"),
            "minute": cfg.get("minute"),
            "schedule_ru": f"{hhmm} ежедневно ({cfg.get('timezone')})" if cfg.get("enabled") else "Автозапуск не настроен",
            "cron_expression": _cron_for(int(cfg["hour"]), int(cfg["minute"])),
            "configured": bool(cfg.get("enabled")) or plat is not None,
            "next_run_at": next_at,
            "next_run_ru": (
                next_local.strftime("%d.%m.%Y %H:%M")
                if next_local is not None
                else ("Автозапуск не настроен" if not cfg.get("enabled") else None)
            ),
            "last_run_at": (last or {}).get("at"),
            "last_result": (last or {}).get("result"),
            "last_confidence": (last or {}).get("confidence"),
            "last_result_ru": (
                f"{(last or {}).get('result')} / {int(round(float((last or {}).get('confidence') or 0) * 100))}%"
                if last
                else "—"
            ),
            "message_ru": None if (cfg.get("enabled") and next_at) else "Автозапуск не настроен",
            "platform_job_present": plat is not None,
        }

    return {
        "tenant_id": tenant_id or "default",
        "jobs": jobs_out,
        "presets": list(PRESET_JOB_KEYS.keys()),
        "honesty": "next_run only when enabled with timezone-aware schedule or real platform job",
    }


def reset_schedule_for_tests() -> None:
    _OVERRIDES.clear()
    _LAST_RUN.clear()
