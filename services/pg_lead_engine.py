# Universal Lead Engine v1 — ingest, dashboard, manager assignment.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from database.models.lead_engine import LeadEngineLead, LeadEngineStatus
from database.session import get_session
from repositories.lead_engine_repository import LeadEngineRepository
from services.automotive_localization import DEFAULT_LANGUAGE, normalize_language
from services.start_payload_parser import StartPayload, parse_start_payload
from services.tenant_routing import ENTRY_LINK_REGISTRY, legacy_vertical_from_args


class LeadEngineV1:
    @staticmethod
    async def ingest_from_deep_link(
        *,
        telegram_user_id: int,
        telegram_username: str | None = None,
        full_name: str | None = None,
        start_args: str | None = None,
        vertical: str | None = None,
        role: str | None = None,
        source_link: str | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        payload = parse_start_payload(start_args)
        link_code = source_link or payload.link_code

        cfg = ENTRY_LINK_REGISTRY.get(link_code or "")
        resolved_vertical = vertical or (cfg.vertical if cfg else None)
        resolved_role = role or (cfg.preset_role if cfg else None)
        resolved_source = link_code or source_link

        if not resolved_vertical:
            legacy = legacy_vertical_from_args(start_args)
            resolved_vertical = legacy or "unknown"

        async with get_session() as session:
            repo = LeadEngineRepository(session)
            row = await repo.create(
                vertical=resolved_vertical,
                role=resolved_role,
                language=normalize_language(language) if language else None,
                source_link=resolved_source,
                utm_source=payload.utm_source,
                utm_campaign=payload.utm_campaign,
                utm_medium=payload.utm_medium,
                referral_code=payload.referral_code,
                telegram_user_id=telegram_user_id,
                telegram_username=telegram_username,
                full_name=full_name,
                status=LeadEngineStatus.NEW.value,
            )
        return LeadEngineV1._snapshot(row)

    @staticmethod
    async def enrich_latest_for_user(
        *,
        telegram_user_id: int,
        source_link: str | None = None,
        language: str | None = None,
        role: str | None = None,
        phone: str | None = None,
    ) -> dict[str, Any] | None:
        async with get_session() as session:
            repo = LeadEngineRepository(session)
            row = await repo.get_latest_for_telegram(
                telegram_user_id,
                source_link=source_link,
            )
            if row is None:
                return None
            updates: dict[str, Any] = {}
            if language is not None:
                updates["language"] = normalize_language(language)
            if role is not None:
                updates["role"] = role
            if phone is not None:
                updates["phone"] = phone
            if not updates:
                return LeadEngineV1._snapshot(row)
            row = await repo.update(row.id, **updates)
            return LeadEngineV1._snapshot(row)

    @staticmethod
    async def assign_manager(
        lead_id: uuid.UUID,
        manager_id: uuid.UUID | None,
    ) -> dict[str, Any] | None:
        async with get_session() as session:
            row = await LeadEngineRepository(session).assign_manager(lead_id, manager_id)
        if row is None:
            return None
        return LeadEngineV1._snapshot(row)

    @staticmethod
    async def update_status(lead_id: uuid.UUID, status: str) -> dict[str, Any] | None:
        if status not in {s.value for s in LeadEngineStatus}:
            raise ValueError(f"Unsupported status: {status}")
        async with get_session() as session:
            row = await LeadEngineRepository(session).update(lead_id, status=status)
        if row is None:
            return None
        return LeadEngineV1._snapshot(row)

    @staticmethod
    async def get_admin_dashboard() -> dict[str, Any]:
        today = LeadEngineRepository.start_of_today()
        week = LeadEngineRepository.start_of_week()

        async with get_session() as session:
            repo = LeadEngineRepository(session)
            leads_today = await repo.count_since(today)
            leads_week = await repo.count_since(week)
            won = await repo.count_by_status(LeadEngineStatus.WON.value)
            lost = await repo.count_by_status(LeadEngineStatus.LOST.value)
            total = await repo.count_since(datetime_min())
            by_source = await repo.group_count(LeadEngineLead.source_link, since=week)
            by_vertical = await repo.group_count(LeadEngineLead.vertical, since=week)
            recent = await repo.list_recent(limit=10)

        closed = won + lost
        conversion_rate = round((won / closed) * 100, 1) if closed else 0.0

        return {
            "leads_today": leads_today,
            "leads_week": leads_week,
            "total": total,
            "won": won,
            "lost": lost,
            "conversion_rate": conversion_rate,
            "by_source": by_source,
            "by_vertical": by_vertical,
            "recent": [LeadEngineV1._snapshot(row) for row in recent],
        }

    @staticmethod
    def format_admin_dashboard(data: dict[str, Any]) -> str:
        lines = [
            "📈 Lead Engine Dashboard",
            "",
            f"📈 Leads today: {data['leads_today']}",
            f"📈 Leads this week: {data['leads_week']}",
            f"📈 Conversion rate: {data['conversion_rate']}%",
            "",
            "📈 Leads by source (week):",
        ]
        if data["by_source"]:
            for source, count in data["by_source"]:
                lines.append(f"  • {source or '—'}: {count}")
        else:
            lines.append("  • —")

        lines.append("")
        lines.append("📈 Leads by vertical (week):")
        if data["by_vertical"]:
            for vertical, count in data["by_vertical"]:
                lines.append(f"  • {vertical or '—'}: {count}")
        else:
            lines.append("  • —")

        lines.append("")
        lines.append(f"Pipeline: {data['total']} total | ✅ {data['won']} won | ❌ {data['lost']} lost")

        recent = data.get("recent") or []
        if recent:
            lines.append("")
            lines.append("Recent leads:")
            for lead in recent[:5]:
                lines.append(
                    f"  • {lead.get('vertical', '—')} | {lead.get('source_link') or '—'} | "
                    f"{lead.get('status')} | @{lead.get('telegram_username') or lead.get('telegram_user_id')}"
                )
        return "\n".join(lines)

    @staticmethod
    def format_lead_list(leads: list[dict[str, Any]]) -> str:
        if not leads:
            return "📋 Leads\n\nСписок пуст."
        lines = ["📋 Leads", ""]
        for lead in leads:
            lines.append(
                f"• {lead['id'][:8]}… | {lead['vertical']} | {lead['status']}\n"
                f"  src: {lead.get('source_link') or '—'} | "
                f"@{lead.get('telegram_username') or lead.get('telegram_user_id')}"
            )
        return "\n".join(lines)

    @staticmethod
    def _snapshot(row: LeadEngineLead) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "vertical": row.vertical,
            "role": row.role,
            "language": row.language,
            "source_link": row.source_link,
            "utm_source": row.utm_source,
            "utm_campaign": row.utm_campaign,
            "utm_medium": row.utm_medium,
            "referral_code": row.referral_code,
            "telegram_user_id": row.telegram_user_id,
            "telegram_username": row.telegram_username,
            "full_name": row.full_name,
            "phone": row.phone,
            "assigned_manager_id": str(row.assigned_manager_id) if row.assigned_manager_id else None,
            "status": row.status,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }


def datetime_min() -> datetime:
    return datetime(1970, 1, 1, tzinfo=timezone.utc)
