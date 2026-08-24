# Scheduler Engine v1 — cron, delayed, and interval jobs with retries and locking.

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.scheduler_engine import (
    JobExecutionStatus,
    JobScheduleType,
    ScheduledJobStatus,
)
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.scheduler_engine_repository import (
    JobExecutionRepository,
    JobFailureRepository,
    ScheduledJobRepository,
)
from repositories.treasury_repository import TreasuryRepository
from repositories.user_role_repository import UserRoleRepository
from services.scheduler_cron import next_cron_run

logger = logging.getLogger(__name__)

SCHEDULER_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})

LOCK_TTL_SECONDS = 300
POLL_INTERVAL_SECONDS = 30
RETRY_DELAYS_SECONDS = (60, 300, 900, 3600)

JobHandler = Callable[[dict[str, Any] | None], Awaitable[dict[str, Any]]]

DEFAULT_JOBS: tuple[dict[str, Any], ...] = (
    {
        "job_key": "nightly.reconciliation",
        "name": "Nightly Reconciliation",
        "description": "Reconcile treasury account balances nightly",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 2 * * *",
    },
    {
        "job_key": "pricing.recalculation",
        "name": "Pricing Recalculation",
        "description": "Refresh market quotes and sync pricing spreads",
        "schedule_type": JobScheduleType.INTERVAL.value,
        "interval_seconds": 3600,
    },
    {
        "job_key": "fx.update",
        "name": "FX Update",
        "description": "Fetch latest FX and exchange quotes",
        "schedule_type": JobScheduleType.INTERVAL.value,
        "interval_seconds": 300,
    },
    {
        "job_key": "fx.intel.morning",
        "name": "FX Intel Morning Brief",
        "description": "EUR/USD + DXY morning analysis profile",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 6 * * 1-5",
    },
    {
        "job_key": "fx.intel.pre_europe",
        "name": "FX Intel Pre-Europe",
        "description": "Analysis before Europe session",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "30 6 * * 1-5",
    },
    {
        "job_key": "fx.intel.pre_us",
        "name": "FX Intel Pre-US",
        "description": "Analysis before US session",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 12 * * 1-5",
    },
    {
        "job_key": "fx.intel.evening",
        "name": "FX Intel Evening Brief",
        "description": "EUR/USD + DXY evening analysis profile",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 20 * * 1-5",
    },
    {
        "job_key": "fx.intel.evaluate",
        "name": "FX Intel Evaluation",
        "description": "Fill analysis evaluation horizons from later market data",
        "schedule_type": JobScheduleType.INTERVAL.value,
        "interval_seconds": 900,
    },
    {
        "job_key": "legal.monitor.morning",
        "name": "Legal Monitor Morning",
        "description": "Lawyer 3.3 watchlist sweep 09:00 Europe/Kyiv (cron UTC approx 06:00)",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 6 * * *",
    },
    {
        "job_key": "legal.monitor.evening",
        "name": "Legal Monitor Evening",
        "description": "Lawyer 3.3 watchlist sweep 18:00 Europe/Kyiv (cron UTC approx 15:00)",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 15 * * *",
    },
    {
        "job_key": "agro.intel.morning",
        "name": "Agro Intelligence Morning",
        "description": "AGRO 1.0 morning report 08:00 Europe/Kyiv (cron UTC approx 05:00)",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 5 * * *",
    },
    {
        "job_key": "agro.intel.evening",
        "name": "Agro Intelligence Evening",
        "description": "AGRO 1.0 evening report 18:00 Europe/Kyiv (cron UTC approx 15:00)",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 15 * * *",
    },
    {
        "job_key": "agro.providers.daily",
        "name": "Agro Providers Daily Ingest",
        "description": "AGRO 1.1 official-source ingest once per day (cron UTC 06:00)",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 6 * * *",
    },
    {
        "job_key": "agro.providers.weather",
        "name": "Agro Weather Provider Checks",
        "description": "AGRO 1.1 weather probes several times per day",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 4,10,16 * * *",
    },
    {
        "job_key": "agro.providers.markets",
        "name": "Agro Market Provider Checks",
        "description": "AGRO 1.1 market/trade probes morning and evening",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 5,15 * * *",
    },
    {
        "job_key": "agro.alerts.evaluate",
        "name": "Agro Price Alert Evaluator",
        "description": "AGRO 1.2 evaluate price alert rules against stored market prices",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 6,18 * * *",
    },
    {
        "job_key": "agro.calendar.reminders",
        "name": "Agro Calendar Reminders",
        "description": "AGRO 1.2 emit reminder notifications for calendar events",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 5,11,17 * * *",
    },
    {
        "job_key": "agro.providers.morning",
        "name": "Agro Providers Morning Ingest",
        "description": "AGRO 1.4 provider ingest 07:30 Europe/Kyiv (cron UTC 04:30)",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "30 4 * * *",
    },
    {
        "job_key": "agro.review.morning",
        "name": "Agro Morning Review",
        "description": "AGRO 1.4 morning review 08:00 Europe/Kyiv (cron UTC 05:00)",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 5 * * *",
    },
    {
        "job_key": "agro.providers.evening",
        "name": "Agro Providers Evening Ingest",
        "description": "AGRO 1.4 provider ingest 18:30 Europe/Kyiv (cron UTC 15:30)",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "30 15 * * *",
    },
    {
        "job_key": "agro.review.evening",
        "name": "Agro Evening Review",
        "description": "AGRO 1.4 evening review 19:00 Europe/Kyiv (cron UTC 16:00)",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 16 * * *",
    },
    {
        "job_key": "agro.providers.dawn",
        "name": "Agro Dawn Ops Refresh",
        "description": "AGRO 1.9 weather/FX/ops 05:45 Europe/Kyiv (cron UTC 02:45)",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "45 2 * * *",
    },
    {
        "job_key": "agro.analysis.morning",
        "name": "Agro Morning Analysis",
        "description": "AGRO 1.9 morning analysis 06:00 Europe/Kyiv (cron UTC 03:00)",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 3 * * *",
    },
    {
        "job_key": "agro.providers.noon",
        "name": "Agro Light Refresh",
        "description": "AGRO 1.9 light refresh 12:00 Europe/Kyiv (cron UTC 09:00)",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 9 * * *",
    },
    {
        "job_key": "agro.providers.full",
        "name": "Agro Full Refresh",
        "description": "AGRO 1.9 full ingest 17:30 Europe/Kyiv (cron UTC 14:30)",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "30 14 * * *",
    },
    {
        "job_key": "agro.analysis.evening",
        "name": "Agro Evening Analysis",
        "description": "AGRO 1.9 evening analysis 18:00 Europe/Kyiv (cron UTC 15:00)",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 15 * * *",
    },
    {
        "job_key": "agro.analysis.weekly",
        "name": "Agro Weekly Analysis",
        "description": "AGRO 1.9 weekly Sunday 09:00 Europe/Kyiv (cron UTC 06:00)",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 6 * * 0",
    },
    {
        "job_key": "agro.analysis.outlook",
        "name": "Agro Monthly Outlook",
        "description": "AGRO 1.9 1–2 month outlook 1st 08:00 Europe/Kyiv (cron UTC 05:00)",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 5 1 * *",
    },
    {
        "job_key": "liquidity.calculation",
        "name": "Liquidity Calculation",
        "description": "Compute liquidity pool status and alerts",
        "schedule_type": JobScheduleType.INTERVAL.value,
        "interval_seconds": 900,
    },
    {
        "job_key": "inventory.aging",
        "name": "Inventory Aging Calculation",
        "description": "Compute inventory aging buckets and metrics",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 3 * * *",
    },
    {
        "job_key": "marketing.publish_queue",
        "name": "Marketing Publication Queue",
        "description": "Process due Telegram, Instagram, Facebook, and TikTok publications",
        "schedule_type": JobScheduleType.INTERVAL.value,
        "interval_seconds": 60,
    },
    {
        "job_key": "marketing_automation.process",
        "name": "Marketing Automation Cycle",
        "description": "Process scheduled posts, repost rules, watermarks, and hashtags",
        "schedule_type": JobScheduleType.INTERVAL.value,
        "interval_seconds": 60,
    },
    {
        "job_key": "sales_pipeline_automation.process",
        "name": "Sales Pipeline Automation",
        "description": "Sync leads, send reminders, and check inactivity alerts",
        "schedule_type": JobScheduleType.INTERVAL.value,
        "interval_seconds": 300,
    },
    {
        "job_key": "analytics_automation.compute",
        "name": "Analytics Automation Compute",
        "description": "Compute leads, conversion, profit, and campaign ROI metrics",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 4 * * *",
    },
    {
        "job_key": "cross_posting.process",
        "name": "Cross Posting Queue",
        "description": "Process due cross-posting jobs across Telegram, Instagram, Facebook, TikTok",
        "schedule_type": JobScheduleType.INTERVAL.value,
        "interval_seconds": 60,
    },
    {
        "job_key": "analytics_engine.aggregate",
        "name": "Analytics Engine Daily Aggregation",
        "description": "Aggregate lead, sales, advertising, and manager statistics",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 5 * * *",
    },
    {
        "job_key": "tenant_billing.monthly",
        "name": "Tenant Billing Monthly",
        "description": "Collect usage and generate tenant invoices",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 5 1 * *",
    },
    {
        "job_key": "revenue_sharing.monthly",
        "name": "Revenue Sharing Monthly",
        "description": "Calculate partner revenue, reports, and settlements",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 6 1 * *",
    },
    {
        "job_key": "auto.ops.morning",
        "name": "Auto Ops Morning Summary",
        "description": "Send Auto OS morning summary to authorized directors",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 7 * * *",
    },
    {
        "job_key": "auto.ops.evening",
        "name": "Auto Ops Evening Summary",
        "description": "Send Auto OS evening summary to authorized directors",
        "schedule_type": JobScheduleType.CRON.value,
        "cron_expression": "0 19 * * *",
    },
)

_defaults_seeded = False


class SchedulerEngineError(Exception):
    pass


class SchedulerEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in SCHEDULER_ROLES for role in roles)

    @staticmethod
    def _job_snapshot(job) -> dict[str, Any]:
        return {
            "id": str(job.id),
            "job_key": job.job_key,
            "name": job.name,
            "description": job.description,
            "schedule_type": job.schedule_type,
            "cron_expression": job.cron_expression,
            "interval_seconds": job.interval_seconds,
            "run_at": job.run_at.isoformat() if job.run_at else None,
            "config": job.config or {},
            "status": job.status,
            "next_run_at": job.next_run_at.isoformat() if job.next_run_at else None,
            "last_run_at": job.last_run_at.isoformat() if job.last_run_at else None,
            "max_retries": job.max_retries,
            "is_one_shot": job.is_one_shot,
            "created_at": job.created_at.isoformat(),
        }

    @staticmethod
    def _execution_snapshot(execution) -> dict[str, Any]:
        return {
            "id": str(execution.id),
            "job_id": str(execution.job_id),
            "status": execution.status,
            "scheduled_at": execution.scheduled_at.isoformat(),
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat()
            if execution.completed_at
            else None,
            "attempt_number": execution.attempt_number,
            "error_message": execution.error_message,
            "next_retry_at": execution.next_retry_at.isoformat()
            if execution.next_retry_at
            else None,
        }

    @staticmethod
    def compute_next_run(job, *, after: datetime | None = None) -> datetime | None:
        now = after or datetime.now(timezone.utc)
        if job.schedule_type == JobScheduleType.CRON.value:
            if not job.cron_expression:
                raise SchedulerEngineError("Cron job missing cron_expression")
            return next_cron_run(job.cron_expression, now)
        if job.schedule_type == JobScheduleType.INTERVAL.value:
            if not job.interval_seconds or job.interval_seconds <= 0:
                raise SchedulerEngineError("Interval job missing interval_seconds")
            return now + timedelta(seconds=job.interval_seconds)
        if job.schedule_type == JobScheduleType.DELAYED.value:
            if job.run_at is None:
                raise SchedulerEngineError("Delayed job missing run_at")
            return job.run_at
        raise SchedulerEngineError(f"Unknown schedule_type: {job.schedule_type}")

    @staticmethod
    async def _run_nightly_reconciliation(config: dict[str, Any] | None) -> dict[str, Any]:
        from services.treasury_engine import TreasuryEngine

        auto_fix = bool((config or {}).get("auto_fix", False))
        async with get_session() as session:
            accounts = await TreasuryRepository(session).list_accounts(limit=500)

        results: list[dict[str, Any]] = []
        for account in accounts:
            report = await TreasuryEngine.balance_reconciliation(
                account.id,
                auto_fix=auto_fix,
            )
            results.append(report)

        unbalanced = [r for r in results if not r.get("is_balanced")]
        return {
            "accounts_checked": len(results),
            "unbalanced_count": len(unbalanced),
            "unbalanced": unbalanced[:10],
        }

    @staticmethod
    async def _run_pricing_recalculation(config: dict[str, Any] | None) -> dict[str, Any]:
        from services.pg_market_data_engine import MarketDataEngineV1

        assets = (config or {}).get("assets")
        return await MarketDataEngineV1.update_quotes(
            OWNER_ID,
            assets=assets,
        )

    @staticmethod
    async def _run_fx_update(config: dict[str, Any] | None) -> dict[str, Any]:
        from services.pg_market_data_engine import MarketDataEngineV1

        assets = (config or {}).get("assets")
        return await MarketDataEngineV1.update_quotes(
            OWNER_ID,
            assets=assets,
        )

    @staticmethod
    async def _run_liquidity_calculation(config: dict[str, Any] | None) -> dict[str, Any]:
        from services.pg_liquidity_engine import LiquidityEngineV1

        return await LiquidityEngineV1.get_status()

    @staticmethod
    async def _run_inventory_aging(config: dict[str, Any] | None) -> dict[str, Any]:
        from services.pg_automotive_analytics_engine import AutomotiveAnalyticsEngineV1

        return await AutomotiveAnalyticsEngineV1.compute_inventory_metrics(OWNER_ID)

    @staticmethod
    async def _run_marketing_publish_queue(config: dict[str, Any] | None) -> dict[str, Any]:
        from services.pg_auto_marketing_engine import AutoMarketingEngineV1

        limit = int((config or {}).get("limit", 20))
        return await AutoMarketingEngineV1.process_due_publications(limit=limit)

    @staticmethod
    async def _run_marketing_automation_process(config: dict[str, Any] | None) -> dict[str, Any]:
        from services.pg_marketing_automation_engine import MarketingAutomationEngineV1

        post_limit = int((config or {}).get("post_limit", 20))
        repost_limit = int((config or {}).get("repost_limit", 10))
        return await MarketingAutomationEngineV1.run_automation_cycle(
            post_limit=post_limit,
            repost_limit=repost_limit,
        )

    @staticmethod
    async def _run_sales_pipeline_automation(config: dict[str, Any] | None) -> dict[str, Any]:
        from services.pg_sales_pipeline_automation_engine import SalesPipelineAutomationEngineV1

        reminder_limit = int((config or {}).get("reminder_limit", 50))
        inactive_days = int((config or {}).get("inactive_days", 3))
        return await SalesPipelineAutomationEngineV1.run_automation_cycle(
            reminder_limit=reminder_limit,
            inactive_days=inactive_days,
        )

    @staticmethod
    async def _run_analytics_automation_compute(config: dict[str, Any] | None) -> dict[str, Any]:
        from services.pg_analytics_automation_engine import AnalyticsAutomationEngineV1

        return await AnalyticsAutomationEngineV1.compute_metrics()

    @staticmethod
    async def _run_cross_posting_process(config: dict[str, Any] | None) -> dict[str, Any]:
        from services.pg_cross_posting_engine import CrossPostingEngineV1

        limit = int((config or {}).get("limit", 20))
        return await CrossPostingEngineV1.process_due_jobs(limit=limit)

    @staticmethod
    async def _run_analytics_engine_aggregate(config: dict[str, Any] | None) -> dict[str, Any]:
        from sqlalchemy import select

        from database.models.partner_tenant_engine import PartnerTenant
        from database.session import get_session
        from services.pg_analytics_engine import AnalyticsEngineV1

        async with get_session() as session:
            result = await session.execute(select(PartnerTenant).limit(1))
            tenant = result.scalar_one_or_none()
        if tenant is None:
            return {"status": "skipped", "reason": "no_tenant"}
        return await AnalyticsEngineV1.aggregate_daily(OWNER_ID, tenant.id)

    @staticmethod
    async def _run_tenant_billing_monthly(config: dict[str, Any] | None) -> dict[str, Any]:
        from services.pg_tenant_billing_engine import TenantBillingEngineV1

        return await TenantBillingEngineV1.run_monthly_billing()

    @staticmethod
    async def _run_revenue_sharing_monthly(config: dict[str, Any] | None) -> dict[str, Any]:
        from services.pg_revenue_sharing_engine import RevenueSharingEngineV1

        return await RevenueSharingEngineV1.run_monthly_cycle()

    @staticmethod

    @staticmethod
    async def _run_fx_intel_profile(preset_id: str) -> dict[str, Any]:
        from services.fx_market_intel import get_fx_market_intel

        result = await get_fx_market_intel().run_full_analysis(
            preset_id=preset_id,
            tenant_id="scheduler",
            timeframe="1H",
        )
        return {
            "ok": bool(result.get("ok")),
            "preset_id": preset_id,
            "direction": (result.get("display") or {}).get("direction"),
            "confidence": (result.get("display") or {}).get("confidence"),
            "persistence": result.get("persistence"),
            "missing_sources": result.get("missing_sources") or [],
        }

    @staticmethod
    async def _run_fx_intel_morning(config: dict[str, Any] | None) -> dict[str, Any]:
        return await SchedulerEngineV1._run_fx_intel_profile("morning")

    @staticmethod
    async def _run_fx_intel_pre_europe(config: dict[str, Any] | None) -> dict[str, Any]:
        return await SchedulerEngineV1._run_fx_intel_profile("pre_europe")

    @staticmethod
    async def _run_fx_intel_pre_us(config: dict[str, Any] | None) -> dict[str, Any]:
        return await SchedulerEngineV1._run_fx_intel_profile("pre_us")

    @staticmethod
    async def _run_fx_intel_evening(config: dict[str, Any] | None) -> dict[str, Any]:
        return await SchedulerEngineV1._run_fx_intel_profile("evening")

    @staticmethod
    async def _run_fx_intel_evaluate(config: dict[str, Any] | None) -> dict[str, Any]:
        """Fill pending evaluation horizons when later market data exists. No fabricated outcomes."""
        from datetime import datetime, timezone

        from database.session import get_session
        from repositories.fx_market_intel_repository import FxMarketIntelRepository
        from services.fx_market_intel.evaluation import compute_move_metrics, due_horizons
        from services.fx_market_intel.yahoo_feed import fetch_bars

        filled = 0
        skipped = 0
        async with get_session() as session:
            repo = FxMarketIntelRepository(session)
            pending = await repo.list_pending_evaluations(limit=50)
            # group by analysis_run_id
            runs: dict[str, list] = {}
            for row in pending:
                runs.setdefault(row.analysis_run_id, []).append(row)
            for run_id, rows in runs.items():
                run = await repo.get_analysis_run(run_id)
                if not run or not run.price_at_analysis or not run.created_at:
                    skipped += len(rows)
                    continue
                due = set(due_horizons(run.created_at))
                bars = await fetch_bars(run.instrument or "EUR/USD", "1H")
                series = bars.get("bars") or []
                try:
                    px0 = float(run.price_at_analysis)
                except Exception:
                    skipped += len(rows)
                    continue
                for ev in rows:
                    if ev.horizon not in due:
                        skipped += 1
                        continue
                    # pick bar closest after horizon
                    target = None
                    created = run.created_at
                    for b in series:
                        try:
                            bt = datetime.fromisoformat(str(b["t"]).replace("Z", "+00:00"))
                        except Exception:
                            continue
                        if bt >= created:
                            target = b
                            # keep scanning until roughly horizon distance
                            delta_h = {"1h": 1, "4h": 4, "1d": 24}.get(ev.horizon, 1)
                            if (bt - created).total_seconds() >= delta_h * 3600 * 0.8:
                                break
                    if not target:
                        skipped += 1
                        continue
                    metrics = compute_move_metrics(
                        price_at=px0,
                        price_after=float(target["c"]),
                        predicted_direction=run.direction,
                        path_highs=[float(target["h"])],
                        path_lows=[float(target["l"])],
                    )
                    await repo.update_evaluation(
                        ev.id,
                        price_after=str(target["c"]),
                        actual_move=metrics["actual_move"],
                        direction_correct=metrics["direction_correct"],
                        signal_outcome=metrics["signal_outcome"],
                        mfe=metrics["mfe"],
                        mae=metrics["mae"],
                        evaluation_status="evaluated",
                        payload=metrics,
                    )
                    filled += 1
        return {"filled": filled, "skipped": skipped}

    @staticmethod
    async def _run_legal_monitor_sweep(config: dict[str, Any] | None) -> dict[str, Any]:
        from services.legal_ops import get_legal_ops_service

        org = (config or {}).get("organization_id")
        svc = get_legal_ops_service()
        return await svc.run_monitor_sweep(org)

    @staticmethod
    async def _run_legal_monitor_morning(config: dict[str, Any] | None) -> dict[str, Any]:
        return await SchedulerEngineV1._run_legal_monitor_sweep(config)

    @staticmethod
    async def _run_legal_monitor_evening(config: dict[str, Any] | None) -> dict[str, Any]:
        return await SchedulerEngineV1._run_legal_monitor_sweep(config)

    @staticmethod
    async def _run_agro_pipeline(
        config: dict[str, Any] | None,
        *,
        fetch: str | None,
        analysis_type: str | None = None,
        reports: list[str] | None = None,
        record_full_refresh: bool = False,
    ) -> dict[str, Any]:
        from services.agro_ops import get_agro_ops_service

        org = (config or {}).get("organization_id")
        return await get_agro_ops_service().run_pipeline(
            org,
            role="platform_owner",
            fetch=fetch,
            analysis_type=analysis_type,
            reports=reports or [],
            record_full_refresh=record_full_refresh,
        )

    @staticmethod
    async def _run_agro_intel_sweep(config: dict[str, Any] | None, kind: str) -> dict[str, Any]:
        return await SchedulerEngineV1._run_agro_pipeline(
            config, fetch=None, analysis_type=kind if kind in {"morning", "evening"} else None, reports=[kind]
        )

    @staticmethod
    async def _run_agro_intel_morning(config: dict[str, Any] | None) -> dict[str, Any]:
        return await SchedulerEngineV1._run_agro_intel_sweep(config, "morning")

    @staticmethod
    async def _run_agro_intel_evening(config: dict[str, Any] | None) -> dict[str, Any]:
        return await SchedulerEngineV1._run_agro_intel_sweep(config, "evening")

    @staticmethod
    async def _run_agro_providers_ingest(config: dict[str, Any] | None, cadence: str | None = None) -> dict[str, Any]:
        fetch = "full" if cadence in (None, "", "full") else cadence
        return await SchedulerEngineV1._run_agro_pipeline(
            config, fetch=fetch, reports=[], record_full_refresh=fetch == "full"
        )

    @staticmethod
    async def _run_agro_providers_light(config: dict[str, Any] | None) -> dict[str, Any]:
        return await SchedulerEngineV1._run_agro_providers_ingest(config, "light")

    @staticmethod
    async def _run_agro_providers_daily(config: dict[str, Any] | None) -> dict[str, Any]:
        return await SchedulerEngineV1._run_agro_providers_ingest(config, None)

    @staticmethod
    async def _run_agro_analysis(config: dict[str, Any] | None, analysis_type: str) -> dict[str, Any]:
        kind = analysis_type if analysis_type in {"morning", "evening", "weekly", "outlook"} else None
        reports = [kind] if kind else []
        return await SchedulerEngineV1._run_agro_pipeline(
            config, fetch=None, analysis_type=analysis_type, reports=reports
        )

    @staticmethod
    async def _run_agro_analysis_morning(config: dict[str, Any] | None) -> dict[str, Any]:
        return await SchedulerEngineV1._run_agro_analysis(config, "morning")

    @staticmethod
    async def _run_agro_analysis_evening(config: dict[str, Any] | None) -> dict[str, Any]:
        return await SchedulerEngineV1._run_agro_analysis(config, "evening")

    @staticmethod
    async def _run_agro_analysis_weekly(config: dict[str, Any] | None) -> dict[str, Any]:
        return await SchedulerEngineV1._run_agro_analysis(config, "weekly")

    @staticmethod
    async def _run_agro_analysis_outlook(config: dict[str, Any] | None) -> dict[str, Any]:
        return await SchedulerEngineV1._run_agro_analysis(config, "outlook")

    @staticmethod
    async def _run_agro_providers_weather(config: dict[str, Any] | None) -> dict[str, Any]:
        return await SchedulerEngineV1._run_agro_providers_ingest(config, "weather")

    @staticmethod
    async def _run_agro_providers_markets(config: dict[str, Any] | None) -> dict[str, Any]:
        return await SchedulerEngineV1._run_agro_providers_ingest(config, "markets")

    @staticmethod
    async def _run_agro_alerts_evaluate(config: dict[str, Any] | None) -> dict[str, Any]:
        from services.agro_ops import get_agro_ops_service

        org = (config or {}).get("organization_id")
        return await get_agro_ops_service().evaluate_alerts(org, role="platform_owner")

    @staticmethod
    async def _run_agro_calendar_reminders(config: dict[str, Any] | None) -> dict[str, Any]:
        from services.agro_ops import get_agro_ops_service

        org = (config or {}).get("organization_id")
        return await get_agro_ops_service().evaluate_reminders(org, role="platform_owner")

    @staticmethod
    async def _run_auto_ops_morning(config: dict[str, Any] | None) -> dict[str, Any]:
        from services.auto_ops import get_auto_ops_service

        org = (config or {}).get("organization_id")
        return await get_auto_ops_service().send_telegram_summary("morning", org)

    @staticmethod
    async def _run_auto_ops_evening(config: dict[str, Any] | None) -> dict[str, Any]:
        from services.auto_ops import get_auto_ops_service

        org = (config or {}).get("organization_id")
        return await get_auto_ops_service().send_telegram_summary("evening", org)

    def job_handlers() -> dict[str, JobHandler]:
        return {
            "nightly.reconciliation": SchedulerEngineV1._run_nightly_reconciliation,
            "pricing.recalculation": SchedulerEngineV1._run_pricing_recalculation,
            "fx.update": SchedulerEngineV1._run_fx_update,
            "fx.intel.morning": SchedulerEngineV1._run_fx_intel_morning,
            "fx.intel.pre_europe": SchedulerEngineV1._run_fx_intel_pre_europe,
            "fx.intel.pre_us": SchedulerEngineV1._run_fx_intel_pre_us,
            "fx.intel.evening": SchedulerEngineV1._run_fx_intel_evening,
            "fx.intel.evaluate": SchedulerEngineV1._run_fx_intel_evaluate,
            "legal.monitor.morning": SchedulerEngineV1._run_legal_monitor_morning,
            "legal.monitor.evening": SchedulerEngineV1._run_legal_monitor_evening,
            "agro.intel.morning": SchedulerEngineV1._run_agro_intel_morning,
            "agro.intel.evening": SchedulerEngineV1._run_agro_intel_evening,
            "agro.providers.daily": SchedulerEngineV1._run_agro_providers_daily,
            "agro.providers.weather": SchedulerEngineV1._run_agro_providers_weather,
            "agro.providers.markets": SchedulerEngineV1._run_agro_providers_markets,
            "agro.alerts.evaluate": SchedulerEngineV1._run_agro_alerts_evaluate,
            "agro.calendar.reminders": SchedulerEngineV1._run_agro_calendar_reminders,
            "agro.providers.morning": SchedulerEngineV1._run_agro_providers_daily,
            "agro.review.morning": SchedulerEngineV1._run_agro_intel_morning,
            "agro.providers.evening": SchedulerEngineV1._run_agro_providers_daily,
            "agro.review.evening": SchedulerEngineV1._run_agro_intel_evening,
            "agro.providers.dawn": SchedulerEngineV1._run_agro_providers_light,
            "agro.providers.noon": SchedulerEngineV1._run_agro_providers_light,
            "agro.providers.full": SchedulerEngineV1._run_agro_providers_daily,
            "agro.analysis.morning": SchedulerEngineV1._run_agro_analysis_morning,
            "agro.analysis.evening": SchedulerEngineV1._run_agro_analysis_evening,
            "agro.analysis.weekly": SchedulerEngineV1._run_agro_analysis_weekly,
            "agro.analysis.outlook": SchedulerEngineV1._run_agro_analysis_outlook,
            "liquidity.calculation": SchedulerEngineV1._run_liquidity_calculation,
            "inventory.aging": SchedulerEngineV1._run_inventory_aging,
            "marketing.publish_queue": SchedulerEngineV1._run_marketing_publish_queue,
            "marketing_automation.process": SchedulerEngineV1._run_marketing_automation_process,
            "sales_pipeline_automation.process": SchedulerEngineV1._run_sales_pipeline_automation,
            "analytics_automation.compute": SchedulerEngineV1._run_analytics_automation_compute,
            "cross_posting.process": SchedulerEngineV1._run_cross_posting_process,
            "analytics_engine.aggregate": SchedulerEngineV1._run_analytics_engine_aggregate,
            "tenant_billing.monthly": SchedulerEngineV1._run_tenant_billing_monthly,
            "revenue_sharing.monthly": SchedulerEngineV1._run_revenue_sharing_monthly,
            "auto.ops.morning": SchedulerEngineV1._run_auto_ops_morning,
            "auto.ops.evening": SchedulerEngineV1._run_auto_ops_evening,
        }

    @staticmethod
    async def ensure_default_jobs() -> list[dict[str, Any]]:
        global _defaults_seeded
        created: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        async with get_session() as session:
            repo = ScheduledJobRepository(session)
            for spec in DEFAULT_JOBS:
                existing = await repo.get_by_key(spec["job_key"])
                if existing is not None:
                    continue
                if spec["schedule_type"] == JobScheduleType.CRON.value:
                    next_run = next_cron_run(spec["cron_expression"], now)
                else:
                    next_run = now + timedelta(seconds=spec["interval_seconds"])
                job = await repo.create(
                    next_run_at=next_run,
                    owner_user_id=OWNER_ID,
                    **spec,
                )
                created.append(SchedulerEngineV1._job_snapshot(job))
            await session.commit()

        if created:
            logger.info("scheduler_default_jobs_seeded", extra={"count": len(created)})
        _defaults_seeded = True
        return created

    @staticmethod
    async def create_cron_job(
        *,
        actor_id: int,
        job_key: str,
        name: str,
        cron_expression: str,
        config: dict | None = None,
        description: str | None = None,
        max_retries: int = 5,
    ) -> dict[str, Any]:
        if not await SchedulerEngineV1.user_can_access(actor_id):
            raise SchedulerEngineError("Access denied")
        if job_key not in SchedulerEngineV1.job_handlers():
            raise SchedulerEngineError(f"Unknown job_key: {job_key}")

        now = datetime.now(timezone.utc)
        next_run = next_cron_run(cron_expression, now)

        async with get_session() as session:
            repo = ScheduledJobRepository(session)
            if await repo.get_by_key(job_key) is not None:
                raise SchedulerEngineError(f"Job already exists: {job_key}")
            job = await repo.create(
                job_key=job_key,
                name=name,
                schedule_type=JobScheduleType.CRON.value,
                cron_expression=cron_expression,
                config=config,
                description=description,
                max_retries=max_retries,
                next_run_at=next_run,
                owner_user_id=actor_id,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                entity_type="scheduled_job",
                entity_id=str(job.id),
                action=AuditAction.CREATE.value,
                new_value={"job_key": job_key, "cron_expression": cron_expression},
            )
            return SchedulerEngineV1._job_snapshot(job)

    @staticmethod
    async def schedule_delayed_job(
        *,
        actor_id: int,
        job_key: str,
        name: str,
        run_at: datetime,
        config: dict | None = None,
        description: str | None = None,
        max_retries: int = 5,
    ) -> dict[str, Any]:
        if not await SchedulerEngineV1.user_can_access(actor_id):
            raise SchedulerEngineError("Access denied")
        if job_key not in SchedulerEngineV1.job_handlers():
            raise SchedulerEngineError(f"Unknown job_key: {job_key}")
        if run_at.tzinfo is None:
            run_at = run_at.replace(tzinfo=timezone.utc)

        async with get_session() as session:
            repo = ScheduledJobRepository(session)
            suffix = uuid.uuid4().hex[:8]
            unique_key = f"{job_key}.{suffix}"
            job = await repo.create(
                job_key=unique_key,
                name=name,
                schedule_type=JobScheduleType.DELAYED.value,
                run_at=run_at,
                config=config,
                description=description,
                max_retries=max_retries,
                next_run_at=run_at,
                owner_user_id=actor_id,
                is_one_shot=True,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                entity_type="scheduled_job",
                entity_id=str(job.id),
                action=AuditAction.CREATE.value,
                new_value={"job_key": unique_key, "run_at": run_at.isoformat()},
            )
            return SchedulerEngineV1._job_snapshot(job)

    @staticmethod
    async def create_interval_job(
        *,
        actor_id: int,
        job_key: str,
        name: str,
        interval_seconds: int,
        config: dict | None = None,
        description: str | None = None,
        max_retries: int = 5,
    ) -> dict[str, Any]:
        if not await SchedulerEngineV1.user_can_access(actor_id):
            raise SchedulerEngineError("Access denied")
        if job_key not in SchedulerEngineV1.job_handlers():
            raise SchedulerEngineError(f"Unknown job_key: {job_key}")
        if interval_seconds <= 0:
            raise SchedulerEngineError("interval_seconds must be positive")

        now = datetime.now(timezone.utc)
        async with get_session() as session:
            repo = ScheduledJobRepository(session)
            if await repo.get_by_key(job_key) is not None:
                raise SchedulerEngineError(f"Job already exists: {job_key}")
            job = await repo.create(
                job_key=job_key,
                name=name,
                schedule_type=JobScheduleType.INTERVAL.value,
                interval_seconds=interval_seconds,
                config=config,
                description=description,
                max_retries=max_retries,
                next_run_at=now + timedelta(seconds=interval_seconds),
                owner_user_id=actor_id,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                entity_type="scheduled_job",
                entity_id=str(job.id),
                action=AuditAction.CREATE.value,
                new_value={"job_key": job_key, "interval_seconds": interval_seconds},
            )
            return SchedulerEngineV1._job_snapshot(job)

    @staticmethod
    async def list_jobs(*, actor_id: int) -> list[dict[str, Any]]:
        if not await SchedulerEngineV1.user_can_access(actor_id):
            raise SchedulerEngineError("Access denied")
        async with get_session() as session:
            jobs = await ScheduledJobRepository(session).list_active()
            return [SchedulerEngineV1._job_snapshot(job) for job in jobs]

    @staticmethod
    async def _execute_job(
        job_id: uuid.UUID,
        *,
        worker_id: str,
        attempt_number: int = 1,
        execution_id: uuid.UUID | None = None,
    ) -> bool:
        handlers = SchedulerEngineV1.job_handlers()
        now = datetime.now(timezone.utc)

        async with get_session() as session:
            job_repo = ScheduledJobRepository(session)
            exec_repo = JobExecutionRepository(session)
            failure_repo = JobFailureRepository(session)

            job = await job_repo.get_by_id(job_id)
            if job is None:
                return False

            handler = handlers.get(job.job_key)
            if handler is None and job.is_one_shot:
                base_key = job.job_key.rsplit(".", 1)[0]
                handler = handlers.get(base_key)
            if handler is None:
                return False

            if execution_id is None:
                execution = await exec_repo.create(
                    job_id=job.id,
                    scheduled_at=job.next_run_at or now,
                    attempt_number=attempt_number,
                    worker_id=worker_id,
                )
            else:
                execution = await exec_repo.get_by_id(execution_id)
                if execution is None:
                    return False
                execution.attempt_number = attempt_number

            await exec_repo.mark_running(execution, worker_id=worker_id, started_at=now)
            await session.commit()
            execution_id = execution.id
            job_config = job.config
            max_retries = job.max_retries

        try:
            result = await handler(job_config)
            completed_at = datetime.now(timezone.utc)
            async with get_session() as session:
                job_repo = ScheduledJobRepository(session)
                exec_repo = JobExecutionRepository(session)
                execution = await exec_repo.get_by_id(execution_id)
                job = await job_repo.get_by_id(job_id)
                if execution is None or job is None:
                    return False

                await exec_repo.mark_completed(
                    execution,
                    completed_at=completed_at,
                    result=result,
                )

                if job.is_one_shot:
                    await job_repo.update_schedule(
                        job,
                        next_run_at=None,
                        last_run_at=completed_at,
                        status=ScheduledJobStatus.COMPLETED.value,
                    )
                else:
                    next_run = SchedulerEngineV1.compute_next_run(job, after=completed_at)
                    await job_repo.update_schedule(
                        job,
                        next_run_at=next_run,
                        last_run_at=completed_at,
                    )

                await job_repo.release_lock(job.id)
                await session.commit()
            return True
        except Exception as exc:
            error_message = str(exc)
            async with get_session() as session:
                job_repo = ScheduledJobRepository(session)
                exec_repo = JobExecutionRepository(session)
                failure_repo = JobFailureRepository(session)
                execution = await exec_repo.get_by_id(execution_id)
                job = await job_repo.get_by_id(job_id)
                if execution is None or job is None:
                    return False

                terminal = attempt_number >= max_retries
                next_retry_at = None
                if not terminal:
                    delay_index = min(attempt_number - 1, len(RETRY_DELAYS_SECONDS) - 1)
                    next_retry_at = now + timedelta(seconds=RETRY_DELAYS_SECONDS[delay_index])

                await exec_repo.mark_failed(
                    execution,
                    error_message=error_message,
                    next_retry_at=next_retry_at,
                    terminal=terminal,
                )
                await failure_repo.create(
                    execution_id=execution.id,
                    job_id=job.id,
                    attempt_number=attempt_number,
                    error_message=error_message,
                    is_terminal=terminal,
                )

                if terminal and job.is_one_shot:
                    await job_repo.update_schedule(
                        job,
                        next_run_at=None,
                        last_run_at=now,
                        status=ScheduledJobStatus.DISABLED.value,
                    )
                elif not terminal:
                    await job_repo.update_schedule(
                        job,
                        next_run_at=next_retry_at,
                        last_run_at=job.last_run_at,
                    )
                else:
                    next_run = SchedulerEngineV1.compute_next_run(job, after=now)
                    await job_repo.update_schedule(
                        job,
                        next_run_at=next_run,
                        last_run_at=job.last_run_at,
                    )

                await job_repo.release_lock(job.id)
                await session.commit()

            logger.exception(
                "scheduler_job_failed",
                extra={
                    "job_id": str(job_id),
                    "execution_id": str(execution_id),
                    "attempt": attempt_number,
                },
            )
            return False

    @staticmethod
    async def process_due_jobs(
        *,
        worker_id: str,
        limit: int = 10,
    ) -> dict[str, int]:
        stats = {"claimed": 0, "completed": 0, "failed": 0, "retries": 0}
        now = datetime.now(timezone.utc)

        async with get_session() as session:
            job_repo = ScheduledJobRepository(session)
            due_jobs = await job_repo.claim_due(
                now=now,
                worker_id=worker_id,
                lock_ttl_seconds=LOCK_TTL_SECONDS,
                limit=limit,
            )
            stats["claimed"] = len(due_jobs)
            job_ids = [job.id for job in due_jobs]
            await session.commit()

        for job_id in job_ids:
            ok = await SchedulerEngineV1._execute_job(job_id, worker_id=worker_id)
            if ok:
                stats["completed"] += 1
            else:
                stats["failed"] += 1

        async with get_session() as session:
            exec_repo = JobExecutionRepository(session)
            retries = await exec_repo.claim_retries(now=now, limit=limit)
            retry_items = [
                (item.id, item.job_id, item.attempt_number + 1) for item in retries
            ]
            await session.commit()

        for execution_id, job_id, attempt_number in retry_items:
            stats["retries"] += 1
            ok = await SchedulerEngineV1._execute_job(
                job_id,
                worker_id=worker_id,
                attempt_number=attempt_number,
                execution_id=execution_id,
            )
            if ok:
                stats["completed"] += 1
            else:
                stats["failed"] += 1

        return stats


class SchedulerWorker:
    """Background worker for due scheduled jobs with graceful shutdown."""

    def __init__(
        self,
        *,
        poll_interval_seconds: float = POLL_INTERVAL_SECONDS,
        batch_size: int = 10,
        worker_id: str | None = None,
    ) -> None:
        self.poll_interval_seconds = poll_interval_seconds
        self.batch_size = batch_size
        self.worker_id = worker_id or f"scheduler-{uuid.uuid4().hex[:12]}"
        self._task: asyncio.Task | None = None
        self._shutdown = asyncio.Event()
        self._started = False

    @property
    def is_running(self) -> bool:
        return self._started and not self._shutdown.is_set()

    async def start(self) -> None:
        if self._started:
            return
        await SchedulerEngineV1.ensure_default_jobs()
        self._shutdown.clear()
        self._started = True
        self._task = asyncio.create_task(self._worker_loop(), name="scheduler-worker")
        logger.info(
            "scheduler_worker_started",
            extra={"worker_id": self.worker_id},
        )

    async def shutdown(self, *, wait: bool = True) -> None:
        if not self._started:
            return
        self._shutdown.set()
        if wait and self._task is not None:
            await asyncio.gather(self._task, return_exceptions=True)
        self._task = None
        self._started = False
        logger.info("scheduler_worker_stopped")

    async def _worker_loop(self) -> None:
        while not self._shutdown.is_set():
            try:
                stats = await SchedulerEngineV1.process_due_jobs(
                    worker_id=self.worker_id,
                    limit=self.batch_size,
                )
                if stats["claimed"] == 0 and stats["retries"] == 0:
                    try:
                        await asyncio.wait_for(
                            self._shutdown.wait(),
                            timeout=self.poll_interval_seconds,
                        )
                    except asyncio.TimeoutError:
                        pass
                else:
                    logger.debug("scheduler_worker_batch", extra=stats)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("scheduler_worker_error")
                try:
                    await asyncio.wait_for(
                        self._shutdown.wait(),
                        timeout=self.poll_interval_seconds,
                    )
                except asyncio.TimeoutError:
                    pass


_default_worker: SchedulerWorker | None = None


def get_default_worker() -> SchedulerWorker:
    global _default_worker
    if _default_worker is None:
        _default_worker = SchedulerWorker()
    return _default_worker
