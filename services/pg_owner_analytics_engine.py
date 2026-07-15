# Owner analytics dashboard metrics for automotive CRM.

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select

from database.session import get_session

logger = logging.getLogger(__name__)


class OwnerAnalyticsEngineV1:
    @staticmethod
    async def get_dashboard_metrics() -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)

        try:
            from database.models.client_request import ClientRequest
        except Exception:
            return OwnerAnalyticsEngineV1._empty_metrics()

        async with get_session() as session:
            total = int(
                (await session.execute(select(func.count()).select_from(ClientRequest))).scalar_one()
            )
            new_today = int(
                (
                    await session.execute(
                        select(func.count())
                        .select_from(ClientRequest)
                        .where(ClientRequest.created_at >= today_start)
                    )
                ).scalar_one()
            )
            active = int(
                (
                    await session.execute(
                        select(func.count())
                        .select_from(ClientRequest)
                        .where(ClientRequest.status.in_(("NEW", "ASSIGNED", "IN_PROGRESS", "WAITING_CLIENT")))
                    )
                ).scalar_one()
            )
            closed = int(
                (
                    await session.execute(
                        select(func.count())
                        .select_from(ClientRequest)
                        .where(ClientRequest.status == "COMPLETED")
                    )
                ).scalar_one()
            )
            cancelled = int(
                (
                    await session.execute(
                        select(func.count())
                        .select_from(ClientRequest)
                        .where(ClientRequest.status == "CANCELLED")
                    )
                ).scalar_one()
            )

            by_manager = (
                await session.execute(
                    select(ClientRequest.manager_id, func.count())
                    .where(ClientRequest.manager_id.is_not(None))
                    .group_by(ClientRequest.manager_id)
                )
            ).all()

            by_type = (
                await session.execute(
                    select(ClientRequest.request_type, func.count()).group_by(ClientRequest.request_type)
                )
            ).all()

        conversion = round((closed / total * 100), 1) if total else 0.0
        return {
            "new_leads_today": new_today,
            "active_leads": active,
            "closed_leads": closed,
            "cancelled_leads": cancelled,
            "total_leads": total,
            "conversion_rate_pct": conversion,
            "average_response_time_min": None,
            "revenue": None,
            "revenue_per_manager": {str(mgr): cnt for mgr, cnt in by_manager},
            "leads_per_source": {src: cnt for src, cnt in by_type},
            "period_start": week_ago.isoformat(),
            "generated_at": now.isoformat(),
        }

    @staticmethod
    def format_dashboard(metrics: dict[str, Any]) -> str:
        lines = [
            "📊 Owner Analytics — Auto CRM",
            "",
            f"🆕 Новые лиды сегодня: {metrics.get('new_leads_today', 0)}",
            f"🟡 Активные: {metrics.get('active_leads', 0)}",
            f"✅ Закрытые: {metrics.get('closed_leads', 0)}",
            f"📈 Конверсия: {metrics.get('conversion_rate_pct', 0)}%",
            "",
            f"Всего заявок: {metrics.get('total_leads', 0)}",
        ]
        by_mgr = metrics.get("revenue_per_manager") or {}
        if by_mgr:
            lines.extend(["", "👤 По менеджерам:"])
            for mgr, cnt in list(by_mgr.items())[:10]:
                lines.append(f"  • {mgr[:8]}…: {cnt}")
        by_src = metrics.get("leads_per_source") or {}
        if by_src:
            lines.extend(["", "📂 По типу:"])
            for src, cnt in by_src.items():
                lines.append(f"  • {src}: {cnt}")
        return "\n".join(lines)

    @staticmethod
    def _empty_metrics() -> dict[str, Any]:
        return {
            "new_leads_today": 0,
            "active_leads": 0,
            "closed_leads": 0,
            "total_leads": 0,
            "conversion_rate_pct": 0.0,
            "revenue_per_manager": {},
            "leads_per_source": {},
        }
