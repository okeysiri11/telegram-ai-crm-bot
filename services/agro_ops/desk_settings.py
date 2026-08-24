"""AGRO 2.0 — desk settings (tabs). Stored on generic settings rows."""

from __future__ import annotations

from typing import Any

from services.agro_ops.rbac import require

DEFAULT_DESK_SETTINGS: dict[str, Any] = {
    "refresh_frequency": "standard",
    "enabled_regions": ["south", "center", "west", "north", "east"],
    "enabled_commodities": ["wheat", "corn", "sunflower", "barley", "rapeseed", "soy"],
    "source_priority": ["official", "manual", "public"],
    "confidence_threshold": 50,
    "report_length": "standard",
    "morning_report_enabled": True,
    "evening_report_enabled": True,
    "analytics_detail": "standard",
    "specialists": {
        "ukraine": True,
        "market": True,
        "price": True,
        "weather": True,
        "crop": True,
        "trade": True,
        "logistics": True,
        "ports": True,
        "risk": True,
        "opportunity": True,
        "chief": True,
    },
    "weather_primary": "weather_provider",
    "weather_backup": "weather_provider_secondary",
    "forecast_horizon_days": 7,
    "crop_impact_enabled": True,
}

SPECIALIST_LABELS = [
    ("ukraine", "Ukraine"),
    ("market", "Markets"),
    ("price", "Prices"),
    ("weather", "Weather"),
    ("crop", "Harvest"),
    ("trade", "Trade"),
    ("logistics", "Logistics"),
    ("ports", "Ports"),
    ("risk", "Risk"),
    ("opportunity", "Opportunity"),
    ("chief", "Chief Agro Analyst"),
]

SETTINGS_TABS = [
    ("general", "ОБЩИЕ"),
    ("sources", "ИСТОЧНИКИ"),
    ("intel", "АГРОРАЗВЕДКА"),
    ("analytics", "АНАЛИТИКА"),
    ("weather", "ПОГОДА"),
    ("schedule", "РАСПИСАНИЕ"),
    ("notifications", "УВЕДОМЛЕНИЯ"),
    ("diagnostics", "ДИАГНОСТИКА"),
]


class AgroOpsDeskSettingsMixin:
    def _desk_settings_row(self, org: str) -> dict[str, Any] | None:
        from services.agro_ops.service import active_only

        return next(
            (s for s in active_only(self._bag(org).get("settings") or []) if s.get("desk_settings")),  # type: ignore[attr-defined]
            None,
        )

    async def get_desk_settings(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.presentation import present_schedule
        from services.agro_ops.providers import DEFAULT_AGRO_SCHEDULE
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        stored = self._desk_settings_row(org) or {}
        item = {**DEFAULT_DESK_SETTINGS, **{k: stored[k] for k in DEFAULT_DESK_SETTINGS if k in stored}}
        specialists = {**DEFAULT_DESK_SETTINGS["specialists"], **(stored.get("specialists") or {})}
        item["specialists"] = specialists
        sched = await self.get_scheduler(org, role)  # type: ignore[attr-defined]
        providers = (await self.providers_status(org, role)).get("items") or []  # type: ignore[attr-defined]
        diagnostics = []
        for p in providers:
            if p.get("error") or str(p.get("http_status") or "") in {"403", "404", "521"} or str(p.get("health_state")) in {"BLOCKED", "FAILED", "METADATA_ONLY"}:
                diagnostics.append(
                    {
                        "provider_id": p.get("id"),
                        "label_ru": p.get("label_ru"),
                        "health_state": p.get("health_state"),
                        "http_status": p.get("http_status"),
                        "error": p.get("error") or p.get("last_error"),
                        "note_ru": p.get("note_ru"),
                        "probe_result": p.get("probe_result"),
                    }
                )
        return {
            "ok": True,
            "tabs": [{"id": i, "label_ru": l} for i, l in SETTINGS_TABS],
            "item": item,
            "specialist_catalog": [{"id": i, "label_en": l, "enabled": bool(specialists.get(i, True))} for i, l in SPECIALIST_LABELS],
            "schedule": present_schedule(sched.get("jobs") or DEFAULT_AGRO_SCHEDULE["jobs"]),
            "schedule_raw": sched,
            "providers": providers,
            "diagnostics": diagnostics,
            "pipeline_version": "AGRO_1_9",
            "ux_version": "AGRO_2_0",
        }

    async def put_desk_settings(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "intel_admin")
        if denied:
            denied = require(role, "admin")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        payload = {**DEFAULT_DESK_SETTINGS, **(body or {}), "desk_settings": True, "name": "agro-desk-settings", "title": "Настройки Агро"}
        existing = self._desk_settings_row(org)
        if existing:
            saved = await self.update_entity(org, "settings", str(existing["id"]), payload, role or "agro_director")  # type: ignore[attr-defined]
        else:
            saved = await self.create_entity(org, "settings", payload, role or "agro_director")  # type: ignore[attr-defined]
        refreshed = await self.get_desk_settings(org, role)
        return {**refreshed, "saved": saved}
