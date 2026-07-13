# Production Readiness Suite — startup validation, dependency checks, diagnostics.

from __future__ import annotations

import asyncio
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import API_HOST, API_PORT, BOT_TOKEN, REDIS_REQUIRED, REDIS_URL
from database.models.production_readiness_engine import AlertSeverity, HealthCheckStatus
from database.session import check_db_health, get_session
from repositories.production_readiness_repository import (
    SystemAlertRepository,
    SystemHealthRepository,
    SystemMetricRepository,
)

SUITE_VERSION = "v1"
CRITICAL_CHECKS = frozenset({"database", "telegram", "scheduler", "api"})


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _check_result(
    name: str,
    *,
    ok: bool,
    detail: str = "",
    payload: dict | None = None,
    degraded: bool = False,
    skipped: bool = False,
) -> dict[str, Any]:
    if skipped:
        status = HealthCheckStatus.SKIPPED.value
    elif ok:
        status = HealthCheckStatus.HEALTHY.value
    elif degraded:
        status = HealthCheckStatus.DEGRADED.value
    else:
        status = HealthCheckStatus.UNHEALTHY.value
    return {
        "name": name,
        "status": status,
        "ok": ok or skipped,
        "ready": ok and not degraded,
        "detail": detail,
        "payload": payload or {},
    }


class ProductionReadinessSuite:
    _startup_validated: bool = False
    _last_diagnostics: dict[str, Any] | None = None

    @classmethod
    async def check_startup(cls) -> dict[str, Any]:
        from database.connection import is_postgres_configured

        checks = {
            "bot_token": bool(BOT_TOKEN),
            "database_configured": is_postgres_configured(),
            "api_host": bool(API_HOST),
            "api_port": API_PORT > 0,
        }
        ok = checks["bot_token"] and checks["api_port"] > 0
        degraded = ok and not checks["database_configured"]
        return _check_result(
            "startup",
            ok=ok,
            degraded=degraded,
            detail="startup configuration validated" if ok else "missing BOT_TOKEN or API config",
            payload=checks,
        )

    @classmethod
    async def check_database(cls) -> dict[str, Any]:
        started = time.perf_counter()
        health = await check_db_health()
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        ok = bool(health.get("ok"))
        detail = health.get("status", "unknown")
        if not ok:
            detail = health.get("error", detail)
        return _check_result(
            "database",
            ok=ok,
            detail=str(detail),
            payload={**health, "duration_ms": duration_ms},
        )

    @classmethod
    async def check_redis(cls) -> dict[str, Any]:
        if not REDIS_URL:
            if REDIS_REQUIRED:
                return _check_result(
                    "redis",
                    ok=False,
                    detail="REDIS_URL not configured but REDIS_REQUIRED=true",
                )
            return _check_result(
                "redis",
                ok=True,
                skipped=True,
                detail="REDIS_URL not configured",
            )

        started = time.perf_counter()
        try:
            parsed = urllib.parse.urlparse(REDIS_URL)
            host = parsed.hostname or "localhost"
            port = parsed.port or 6379
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=3,
            )
            writer.write(b"PING\r\n")
            await writer.drain()
            response = await asyncio.wait_for(reader.readline(), timeout=3)
            writer.close()
            await writer.wait_closed()
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            ok = response.startswith(b"+PONG")
            return _check_result(
                "redis",
                ok=ok,
                detail="PONG" if ok else response.decode(errors="replace").strip(),
                payload={"host": host, "port": port, "duration_ms": duration_ms},
            )
        except Exception as exc:
            return _check_result(
                "redis",
                ok=False,
                detail=str(exc),
                payload={"url_configured": True},
            )

    @classmethod
    async def check_api(cls) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            import aiohttp

            url = f"http://127.0.0.1:{API_PORT}/liveness"
            timeout = aiohttp.ClientTimeout(total=3)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    body = await response.json()
                    duration_ms = round((time.perf_counter() - started) * 1000, 2)
                    ok = response.status == 200 and body.get("status") == "alive"
                    return _check_result(
                        "api",
                        ok=ok,
                        detail=f"HTTP {response.status}",
                        payload={
                            "host": API_HOST,
                            "port": API_PORT,
                            "duration_ms": duration_ms,
                            "body": body,
                        },
                    )
        except Exception as exc:
            return _check_result(
                "api",
                ok=False,
                detail=str(exc),
                payload={"host": API_HOST, "port": API_PORT},
            )

    @classmethod
    async def check_scheduler(cls) -> dict[str, Any]:
        try:
            from services.pg_scheduler_engine import get_default_worker

            worker = get_default_worker()
            running = worker.is_running
            return _check_result(
                "scheduler",
                ok=running,
                degraded=not running,
                detail="worker running" if running else "worker not started",
                payload={"worker_id": worker.worker_id, "running": running},
            )
        except Exception as exc:
            return _check_result("scheduler", ok=False, detail=str(exc))

    @classmethod
    async def check_telegram(cls) -> dict[str, Any]:
        if not BOT_TOKEN:
            return _check_result("telegram", ok=False, detail="BOT_TOKEN missing")

        started = time.perf_counter()
        bot = None
        try:
            from aiogram import Bot

            bot = Bot(token=BOT_TOKEN)
            me = await bot.get_me()
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            return _check_result(
                "telegram",
                ok=True,
                detail=f"@{me.username}" if me.username else me.full_name,
                payload={
                    "bot_id": me.id,
                    "username": me.username,
                    "duration_ms": duration_ms,
                },
            )
        except Exception as exc:
            return _check_result("telegram", ok=False, detail=str(exc))
        finally:
            if bot is not None:
                await bot.session.close()

    @classmethod
    async def check_market_sources(cls) -> dict[str, Any]:
        try:
            from database.models.market_data import MarketSourceCode
            from services.pg_market_data_engine import REFERENCE_ONLY_SOURCES

            active_refs = {
                MarketSourceCode.OKX.value,
                MarketSourceCode.WHITEBIT.value,
            }
            missing = active_refs - REFERENCE_ONLY_SOURCES
            engine_src = Path(__file__).resolve().parent / "pg_market_data_engine.py"
            binance_removed = "MarketSourceCode.BINANCE" not in engine_src.read_text(encoding="utf-8")
            ok = not missing and binance_removed
            detail = "OKX/WhiteBIT reference-only; Binance removed"
            if missing:
                detail = f"missing reference sources: {', '.join(sorted(missing))}"
            elif not binance_removed:
                detail = "Binance still referenced in market data engine"
            return _check_result(
                "market_sources",
                ok=ok,
                degraded=bool(missing) and not binance_used,
                detail=detail,
                payload={
                    "reference_only": sorted(REFERENCE_ONLY_SOURCES),
                    "okx": MarketSourceCode.OKX.value in REFERENCE_ONLY_SOURCES,
                    "whitebit": MarketSourceCode.WHITEBIT.value in REFERENCE_ONLY_SOURCES,
                },
            )
        except Exception as exc:
            return _check_result("market_sources", ok=False, detail=str(exc))

    @classmethod
    async def run_dependency_validation(cls, *, persist: bool = True) -> dict[str, Any]:
        started = time.perf_counter()
        checks = await asyncio.gather(
            cls.check_startup(),
            cls.check_database(),
            cls.check_redis(),
            cls.check_api(),
            cls.check_scheduler(),
            cls.check_telegram(),
            cls.check_market_sources(),
        )
        by_name = {item["name"]: item for item in checks}
        critical_ready = True
        for name in CRITICAL_CHECKS:
            item = by_name.get(name, {})
            if item.get("status") == HealthCheckStatus.UNHEALTHY.value:
                critical_ready = False
                break
        if REDIS_URL or REDIS_REQUIRED:
            redis = by_name.get("redis", {})
            if redis.get("status") == HealthCheckStatus.UNHEALTHY.value:
                critical_ready = False

        unhealthy = [
            name for name, item in by_name.items()
            if item.get("status") == HealthCheckStatus.UNHEALTHY.value
        ]
        degraded = [
            name for name, item in by_name.items()
            if item.get("status") == HealthCheckStatus.DEGRADED.value
        ]
        duration_ms = round((time.perf_counter() - started) * 1000, 2)

        payload = {
            "suite": "production_readiness",
            "version": SUITE_VERSION,
            "checked_at": _now().isoformat(),
            "ready": critical_ready,
            "ok": not unhealthy,
            "status": (
                "healthy" if critical_ready and not degraded
                else "degraded" if critical_ready
                else "unhealthy"
            ),
            "duration_ms": duration_ms,
            "checks": by_name,
            "unhealthy": unhealthy,
            "degraded": degraded,
        }
        cls._last_diagnostics = payload
        if persist:
            await cls._persist_run(payload)
        return payload

    @classmethod
    async def _persist_run(cls, payload: dict[str, Any]) -> None:
        now = _now()
        checks = payload.get("checks") or {}
        async with get_session() as session:
            health_repo = SystemHealthRepository(session)
            metric_repo = SystemMetricRepository(session)
            alert_repo = SystemAlertRepository(session)

            for name, item in checks.items():
                await health_repo.record(
                    check_name=name,
                    status=item.get("status", HealthCheckStatus.UNHEALTHY.value),
                    detail=item.get("detail"),
                    payload=item.get("payload"),
                    checked_at=now,
                    suite_version=SUITE_VERSION,
                )
                if item.get("status") == HealthCheckStatus.HEALTHY.value:
                    await alert_repo.resolve_for_component(name, resolved_at=now)
                elif item.get("status") == HealthCheckStatus.UNHEALTHY.value:
                    await alert_repo.create(
                        alert_type="dependency_failure",
                        severity=AlertSeverity.CRITICAL.value,
                        component=name,
                        message=item.get("detail") or f"{name} unhealthy",
                        payload=item.get("payload"),
                    )
                elif item.get("status") == HealthCheckStatus.DEGRADED.value:
                    await alert_repo.create(
                        alert_type="degradation",
                        severity=AlertSeverity.WARNING.value,
                        component=name,
                        message=item.get("detail") or f"{name} degraded",
                        payload=item.get("payload"),
                    )

            await metric_repo.record(
                metric_name="readiness_duration_ms",
                metric_value=payload.get("duration_ms", 0),
                unit="ms",
                recorded_at=now,
                tags={"suite": SUITE_VERSION},
            )
            await metric_repo.record(
                metric_name="readiness_ready",
                metric_value=1 if payload.get("ready") else 0,
                unit="boolean",
                recorded_at=now,
            )
            unresolved = await alert_repo.count_unresolved()
            await metric_repo.record(
                metric_name="system_alerts_unresolved",
                metric_value=sum(unresolved.values()),
                unit="count",
                recorded_at=now,
                tags=unresolved,
            )

    @classmethod
    async def validate_startup(cls) -> dict[str, Any]:
        result = await cls.run_dependency_validation(persist=True)
        cls._startup_validated = bool(result.get("ready"))
        return result

    @classmethod
    async def run_diagnostics(cls) -> dict[str, Any]:
        return await cls.run_dependency_validation(persist=True)

    @classmethod
    async def liveness(cls) -> dict[str, Any]:
        return {
            "status": "alive",
            "suite": "production_readiness",
            "version": SUITE_VERSION,
            "timestamp": _now().isoformat(),
            "startup_validated": cls._startup_validated,
        }

    @classmethod
    async def readiness(cls) -> dict[str, Any]:
        payload = await cls.run_dependency_validation(persist=True)
        return {
            "status": "ready" if payload.get("ready") else "not_ready",
            "ready": payload.get("ready", False),
            "checks": {
                name: item.get("status")
                for name, item in (payload.get("checks") or {}).items()
            },
            "unhealthy": payload.get("unhealthy", []),
            "degraded": payload.get("degraded", []),
            "checked_at": payload.get("checked_at"),
            "duration_ms": payload.get("duration_ms"),
        }

    @classmethod
    async def health(cls) -> dict[str, Any]:
        payload = await cls.run_dependency_validation(persist=True)
        alerts = await cls.get_active_alerts()
        return {
            **payload,
            "alerts": alerts,
        }

    @classmethod
    async def get_active_alerts(cls) -> list[dict[str, Any]]:
        async with get_session() as session:
            rows = await SystemAlertRepository(session).list_unresolved(limit=20)
        return [
            {
                "id": str(row.id),
                "alert_type": row.alert_type,
                "severity": row.severity,
                "component": row.component,
                "message": row.message,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]

    @classmethod
    def format_report(cls, payload: dict[str, Any]) -> str:
        icons = {
            HealthCheckStatus.HEALTHY.value: "🟢",
            HealthCheckStatus.DEGRADED.value: "🟡",
            HealthCheckStatus.UNHEALTHY.value: "🔴",
            HealthCheckStatus.SKIPPED.value: "⚪",
        }
        lines = [
            "🏭 Production Readiness",
            "",
            f"Status: {payload.get('status', 'unknown').upper()}",
            f"Ready: {'yes' if payload.get('ready') else 'no'}",
            f"Duration: {payload.get('duration_ms', 0)} ms",
            "",
            "Dependencies:",
        ]
        for name, item in (payload.get("checks") or {}).items():
            status = item.get("status", "unknown")
            detail = item.get("detail", "")
            lines.append(f"{icons.get(status, '⚪')} {name}: {status} — {detail}")
        unhealthy = payload.get("unhealthy") or []
        if unhealthy:
            lines.append(f"\nUnhealthy: {', '.join(unhealthy)}")
        return "\n".join(lines)
