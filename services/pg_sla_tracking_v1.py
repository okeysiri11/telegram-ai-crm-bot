# SLA Tracking v1 — response time, close time, manager performance.

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from database.models.sla_tracking_v1 import (
    SLA_GREEN_MAX_MINUTES,
    SLA_YELLOW_MAX_MINUTES,
    SlaTrafficLight,
)
from database.session import get_session
from repositories.sla_tracking_v1_repository import SlaTrackingV1Repository

logger = logging.getLogger(__name__)

CONTACT_STAGES = frozenset({"CONTACTED", "QUALIFIED", "OFFER_SENT", "MATCHING"})


class SlaTrackingV1:
    @staticmethod
    def traffic_light_emoji(minutes: int | None) -> str:
        if minutes is None:
            return "⚪"
        if minutes < SLA_GREEN_MAX_MINUTES:
            return "🟢"
        if minutes <= SLA_YELLOW_MAX_MINUTES:
            return "🟡"
        return "🔴"

    @staticmethod
    def traffic_light_code(minutes: int) -> str:
        if minutes < SLA_GREEN_MAX_MINUTES:
            return SlaTrafficLight.GREEN.value
        if minutes <= SLA_YELLOW_MAX_MINUTES:
            return SlaTrafficLight.YELLOW.value
        return SlaTrafficLight.RED.value

    @staticmethod
    def _minutes_between(start: datetime, end: datetime) -> int:
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        return max(int((end - start).total_seconds() // 60), 0)

    @staticmethod
    async def on_lead_created(
        *,
        lead_id: uuid.UUID,
        vertical: str,
        created_at: datetime | None = None,
        manager_id: uuid.UUID | None = None,
    ) -> None:
        try:
            async with get_session() as session:
                repo = SlaTrackingV1Repository(session)
                existing = await repo.get_by_lead_id(lead_id)
                if existing is not None:
                    return
                await repo.create(
                    lead_id=lead_id,
                    vertical=vertical,
                    lead_created_at=created_at or datetime.now(timezone.utc),
                    manager_id=manager_id,
                )
        except Exception:
            logger.exception("SLA on_lead_created failed lead=%s", lead_id)

    @staticmethod
    async def on_manager_assigned(
        lead_id: uuid.UUID,
        manager_id: uuid.UUID | None,
    ) -> None:
        try:
            now = datetime.now(timezone.utc)
            async with get_session() as session:
                repo = SlaTrackingV1Repository(session)
                row = await repo.get_by_lead_id(lead_id)
                if row is None:
                    return
                await repo.update(
                    row.id,
                    manager_id=manager_id,
                    manager_assigned_at=now if manager_id else None,
                )
        except Exception:
            logger.exception("SLA on_manager_assigned failed lead=%s", lead_id)

    @staticmethod
    async def on_first_contact(lead_id: uuid.UUID, *, at: datetime | None = None) -> None:
        try:
            now = at or datetime.now(timezone.utc)
            async with get_session() as session:
                repo = SlaTrackingV1Repository(session)
                row = await repo.get_by_lead_id(lead_id)
                if row is None or row.first_contact_at is not None:
                    return
                minutes = SlaTrackingV1._minutes_between(row.lead_created_at, now)
                await repo.update(
                    row.id,
                    first_contact_at=now,
                    first_response_minutes=minutes,
                    response_traffic_light=SlaTrackingV1.traffic_light_code(minutes),
                    is_overdue=False,
                )
        except Exception:
            logger.exception("SLA on_first_contact failed lead=%s", lead_id)

    @staticmethod
    async def on_pipeline_stage(lead_id: uuid.UUID, stage_code: str) -> None:
        if stage_code in CONTACT_STAGES:
            await SlaTrackingV1.on_first_contact(lead_id)

    @staticmethod
    async def on_lead_status(lead_id: uuid.UUID, status: str) -> None:
        if status == "CONTACTED":
            await SlaTrackingV1.on_first_contact(lead_id)

    @staticmethod
    async def on_deal_linked(
        lead_id: uuid.UUID,
        deal_id: uuid.UUID,
    ) -> None:
        try:
            async with get_session() as session:
                repo = SlaTrackingV1Repository(session)
                await repo.update_by_lead(lead_id, deal_id=deal_id)
        except Exception:
            logger.exception("SLA on_deal_linked failed lead=%s deal=%s", lead_id, deal_id)

    @staticmethod
    async def on_deal_closed(
        *,
        deal_id: uuid.UUID,
        lead_id: uuid.UUID | None,
        closed_at: datetime | None = None,
    ) -> None:
        try:
            now = closed_at or datetime.now(timezone.utc)
            async with get_session() as session:
                repo = SlaTrackingV1Repository(session)
                if lead_id:
                    await repo.update_by_lead(
                        lead_id,
                        deal_id=deal_id,
                        deal_closed_at=now,
                    )
        except Exception:
            logger.exception("SLA on_deal_closed failed deal=%s", deal_id)

    @staticmethod
    async def get_owner_metrics() -> dict[str, Any]:
        async with get_session() as session:
            repo = SlaTrackingV1Repository(session)
            await repo.refresh_overdue_flags()
            manager_stats = await repo.manager_stats_simple()
            ranked = [
                m for m in manager_stats
                if m.get("avg_response_minutes") is not None
            ]
            ranked.sort(key=lambda m: m["avg_response_minutes"])
            best = ranked[0] if ranked else None
            worst = ranked[-1] if len(ranked) > 1 else None

            conversion_ranked = sorted(
                manager_stats,
                key=lambda m: m.get("conversion_rate", 0),
                reverse=True,
            )
            best_conversion = conversion_ranked[0] if conversion_ranked else None

            return {
                "avg_response_minutes": await repo.avg_response_minutes(),
                "avg_close_minutes": await repo.avg_close_minutes(),
                "overdue_leads": await repo.count_overdue(),
                "sla_violations": await repo.count_sla_violations(),
                "traffic_lights": await repo.traffic_light_counts(),
                "best_manager": best,
                "worst_manager": worst,
                "best_conversion_manager": best_conversion,
                "manager_stats": manager_stats,
                "overdue_sample": [
                    {
                        "lead_id": str(r.lead_id),
                        "vertical": r.vertical,
                        "minutes_waiting": SlaTrackingV1._minutes_between(
                            r.lead_created_at,
                            datetime.now(timezone.utc),
                        ),
                    }
                    for r in await repo.list_overdue(limit=5)
                ],
            }

    @staticmethod
    def format_owner_sla_analytics(data: dict[str, Any]) -> str:
        sla = data.get("sla") or {}
        avg_resp = sla.get("avg_response_minutes")
        avg_close = sla.get("avg_close_minutes")
        lights = sla.get("traffic_lights") or {}

        lines = [
            "⏱ SLA Analytics",
            "",
            f"Average response time: {avg_resp if avg_resp is not None else '—'} min",
            f"Average close time: {avg_close if avg_close is not None else '—'} min",
            "",
            "Traffic light (responses):",
            f"  🟢 <15 min: {lights.get('green', 0)}",
            f"  🟡 15-60 min: {lights.get('yellow', 0)}",
            f"  🔴 >60 min: {lights.get('red', 0)}",
            "",
            f"Overdue leads: {sla.get('overdue_leads', 0)}",
            f"SLA violations: {sla.get('sla_violations', 0)}",
            "",
        ]

        best = sla.get("best_manager")
        worst = sla.get("worst_manager")
        if best:
            lines.append(
                f"🏆 Best manager (response): {best['manager_id'][:8]}… "
                f"({best['avg_response_minutes']} min)"
            )
        else:
            lines.append("🏆 Best manager: —")
        if worst and worst != best:
            lines.append(
                f"⚠️ Worst manager (response): {worst['manager_id'][:8]}… "
                f"({worst['avg_response_minutes']} min)"
            )
        else:
            lines.append("⚠️ Worst manager: —")

        best_conv = sla.get("best_conversion_manager")
        if best_conv:
            lines.append(
                f"📈 Best conversion: {best_conv['manager_id'][:8]}… "
                f"({best_conv['conversion_rate']}%)"
            )

        overdue = sla.get("overdue_sample") or []
        if overdue:
            lines.append("")
            lines.append("Overdue sample:")
            for item in overdue:
                lines.append(
                    f"  • {item['vertical']}: {item['lead_id'][:8]}… "
                    f"({item['minutes_waiting']} min waiting)"
                )

        lines.append("")
        lines.append("Manager performance:")
        for mgr in (sla.get("manager_stats") or [])[:5]:
            avg = mgr.get("avg_response_minutes")
            avg_label = f"{avg} min" if avg is not None else "—"
            lines.append(
                f"  • {mgr['manager_id'][:8]}…: "
                f"resp {avg_label}, conv {mgr.get('conversion_rate', 0)}%"
            )
        if not sla.get("manager_stats"):
            lines.append("  • —")

        return "\n".join(lines)

    @staticmethod
    def format_response_badge(minutes: int | None) -> str:
        emoji = SlaTrackingV1.traffic_light_emoji(minutes)
        if minutes is None:
            return f"{emoji} pending"
        return f"{emoji} {minutes} min"
