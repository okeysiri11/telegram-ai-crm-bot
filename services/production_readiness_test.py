# Production Readiness Suite tests.

from __future__ import annotations

import asyncio

from services.production_readiness_suite import ProductionReadinessSuite, SUITE_VERSION


async def run_liveness_test() -> dict:
    payload = await ProductionReadinessSuite.liveness()
    checks = {
        "status_alive": payload.get("status") == "alive",
        "has_version": payload.get("version") == SUITE_VERSION,
        "has_timestamp": bool(payload.get("timestamp")),
    }
    return {"ok": all(checks.values()), "checks": checks, "payload": payload}


async def run_dependency_checks_test() -> dict:
    payload = await ProductionReadinessSuite.run_dependency_validation(persist=False)
    checks = payload.get("checks") or {}
    required = {"startup", "database", "redis", "api", "scheduler", "telegram"}
    checks_result = {
        "all_checks_present": required.issubset(set(checks)),
        "has_status": bool(payload.get("status")),
        "has_duration": "duration_ms" in payload,
    }
    return {
        "ok": all(checks_result.values()),
        "checks": checks_result,
        "status": payload.get("status"),
    }


async def run_report_format_test() -> dict:
    payload = await ProductionReadinessSuite.run_dependency_validation(persist=False)
    report = ProductionReadinessSuite.format_report(payload)
    checks = {
        "report_nonempty": bool(report),
        "mentions_status": "Status:" in report,
        "mentions_dependencies": "Dependencies:" in report,
    }
    return {"ok": all(checks.values()), "checks": checks}


async def run_production_readiness_test_suite() -> dict:
    liveness = await run_liveness_test()
    dependencies = await run_dependency_checks_test()
    report = await run_report_format_test()
    ok = liveness.get("ok") and dependencies.get("ok") and report.get("ok")
    return {
        "ok": ok,
        "liveness": liveness,
        "dependencies": dependencies,
        "report": report,
    }


def run_production_readiness_tests() -> dict:
    return asyncio.run(run_production_readiness_test_suite())
