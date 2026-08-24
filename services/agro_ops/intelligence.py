"""АГРО-РАЗВЕДКА — provider-based intelligence (AGRO Production 1.0).

Provider registry with HONEST statuses: no source is ever presented as
connected until real credentials/feeds are configured. Reports are built
from two ingredients only:
  1) real internal operational data (payments, deliveries, contracts, tasks);
  2) manually imported intelligence items (kind="intel_item" via manual provider).
External sections without a configured provider show
«Требуется подключение источника». Nothing is fabricated.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from services.agro_ops.providers import PROVIDER_CATALOG
from services.agro_ops.rbac import normalize_role, require

FRESHNESS_STATUSES = ("LIVE", "DELAYED", "STALE", "NOT_CONFIGURED", "UNAVAILABLE", "CONNECTED", "DEGRADED", "ERROR")

REPORT_SECTIONS = [
    ("ukraine", "Украина"),
    ("world", "Мировые рынки"),
    ("prices", "Цены"),
    ("harvest", "Урожай"),
    ("weather", "Погода"),
    ("trade", "Экспорт / импорт"),
    ("logistics", "Логистика"),
    ("risks", "Риски"),
    ("opportunities", "Возможности"),
    ("today", "Что важно сегодня"),
]

MARKET_GROUPS = ["ЕС", "Чёрное море", "Ближний Восток", "Северная Африка", "Азия", "Кавказ", "Балканы"]

AGENTS = [
    ("ukraine", "Агент по Украине", "Урожай, экспорт, логистика, регуляторика Украины"),
    ("market", "Рыночный агент", "Сравнение рынков и официальных котировок"),
    ("trade", "Торговый агент", "Международные потоки и рынки сбыта"),
    ("price", "Ценовой агент", "Цены и котировки только из нормализованных наблюдений"),
    ("weather", "Погодный агент", "Погода и влияние на культуры"),
    ("crop", "Агент по урожаю", "Предложение и производство"),
    ("logistics", "Логистический агент", "Ставки, маршруты, порты — без выдуманного фрахта"),
    ("ports", "Портовый агент", "Порты и терминалы"),
    ("global", "Агент мировых рынков", "FAO / EU / AMIS / World Bank"),
    ("risk", "Риск-агент", "Операционные, рыночные, погодные, контрагентские риски"),
    ("opportunity", "Агент возможностей", "Потенциальный спред, не гарантированная прибыль"),
    ("chief", "Главный агро-аналитик", "Сводный вывод"),
]

REPORT_TYPE_MAP = {
    "morning": "MORNING",
    "evening": "EVENING",
    "weekly": "WEEKLY",
    "outlook": "MONTHLY_1_2",
    "morning_on_demand": "MORNING_ON_DEMAND",
}

MORNING_SECTIONS = [
    ("today", "Что важно сегодня"),
    ("ukraine", "Украина"),
    ("prices", "Цены и рынки"),
    ("trade", "Экспорт / импорт"),
    ("weather", "Погода / агрометео"),
    ("world", "Мировые рынки"),
    ("harvest", "Урожай / предложение"),
    ("risks", "Риски"),
    ("opportunities", "Возможности"),
    ("watch", "Что отслеживать сегодня"),
]

EVENING_SECTIONS = [
    ("changed", "Что изменилось с утра"),
    ("new_data", "Новые данные"),
    ("prices", "Цены"),
    ("trade", "Экспорт"),
    ("weather", "Погода"),
    ("world", "Мировые рынки"),
    ("risks", "Риски"),
    ("opportunities", "Возможности"),
    ("tomorrow", "Что важно завтра"),
]

NOT_CONFIGURED_RU = "Требуется подключение источника"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgroOpsIntelMixin:
    """Mixed into AgroOpsService."""

    # ------------------------------------------------------------------
    # manual intelligence import (dedupe by content fingerprint)
    # ------------------------------------------------------------------

    async def import_intel_item(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "intel")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        title = str(body.get("title") or "").strip()
        if not title:
            return {"ok": False, "error": "validation", "message_ru": "Укажите заголовок сообщения"}
        section = str(body.get("section") or "world")
        if section not in {s for s, _ in REPORT_SECTIONS}:
            section = "world"
        fingerprint = hashlib.sha256(
            f"{title}|{body.get('source') or ''}|{body.get('summary') or ''}".encode("utf-8")
        ).hexdigest()
        bag = self._bag(org)  # type: ignore[attr-defined]
        dup = next(
            (i for i in bag["report"] if i.get("fingerprint") == fingerprint and i.get("record_type") == "intel_item"),
            None,
        )
        if dup:
            return {"ok": False, "error": "duplicate", "message_ru": "Такое сообщение уже импортировано (дедупликация)", "item": dup}
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "record_type": "intel_item",
            "title": title,
            "summary": body.get("summary"),
            "detail": body.get("detail"),
            "section": section,
            "source": body.get("source") or "manual_import",
            "source_url": body.get("source_url"),
            "crops": body.get("crops") or [],
            "regions": body.get("regions") or [],
            "confidence": body.get("confidence") or "medium",
            "fingerprint": fingerprint,
            "published_at": body.get("published_at") or _now(),
            "status": "active",
            "created_at": _now(),
        }
        saved = await self._persist("report", item)  # type: ignore[attr-defined]
        bag["report"].insert(0, saved)
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org, entity_type="intel_item", entity_id=saved["id"], action="created",
            summary=f"Импортировано сообщение разведки: {title}", role=role,
        )
        return {"ok": True, "item": saved}

    def _intel_items(self, org: str) -> list[dict[str, Any]]:
        from services.agro_ops.service import active_only

        return [
            r for r in active_only(self._bag(org)["report"])  # type: ignore[attr-defined]
            if r.get("record_type") == "intel_item"
        ]

    OBS_SECTION = {
        "trade_observation": ("trade", "ukraine"),
        "crop_observation": ("harvest", "world"),
        "weather_observation": ("weather",),
        "price_observation": ("prices",),
        "market_observation": ("world", "prices"),
    }

    def _observation_items(self, org: str) -> list[dict[str, Any]]:
        from services.agro_ops.service import active_only

        bag = self._bag(org)  # type: ignore[attr-defined]
        items: list[dict[str, Any]] = []
        for kind, sections in self.OBS_SECTION.items():
            for row in active_only(bag.get(kind) or []):
                title = str(row.get("title") or row.get("raw_value") or row.get("name") or "").strip()
                if not title and row.get("normalized_value") not in (None, ""):
                    title = f"{row.get('commodity') or kind} {row.get('normalized_value')} {row.get('unit') or ''}".strip()
                if not title:
                    continue
                extra_sections = tuple(row.get("sections") or ()) or sections
                if str(row.get("country") or "") in {"UA", "UKR", "Ukraine"} and "ukraine" not in extra_sections:
                    extra_sections = tuple(dict.fromkeys([*extra_sections, "ukraine"]))
                items.append(
                    {
                        **row,
                        "record_kind": kind,
                        "sections": extra_sections,
                        "text": title,
                        "source": row.get("provider_id") or row.get("source") or "official",
                        "source_url": row.get("source_url"),
                        "published_at": row.get("published_at") or row.get("ingested_at"),
                        "confidence": row.get("confidence") or "medium",
                    }
                )
        return items

    # ------------------------------------------------------------------
    # reports (morning / evening / weekly / outlook)
    # ------------------------------------------------------------------

    def _internal_bullets(self, org: str) -> dict[str, list[dict[str, Any]]]:
        """Real internal operational facts — the only guaranteed-true data."""
        from services.agro_ops.service import active_only

        bag = self._bag(org)  # type: ignore[attr-defined]
        today = datetime.now(timezone.utc).date().isoformat()
        bullets: dict[str, list[dict[str, Any]]] = {"today": [], "risks": [], "logistics": []}

        fin = self.finance_summary_data(org)
        if fin["overdue"]:
            bullets["risks"].append(
                {"text": f"Просроченные счета: {len(fin['overdue'])} на сумму {fin['overdue_total']}", "source": "ADOS (внутренние данные)", "confidence": "high"}
            )
        for inv in fin["receivables"][:3]:
            if str(inv.get("due_at") or "")[:10] == today:
                bullets["today"].append(
                    {"text": f"Сегодня ожидается оплата: {inv.get('title')} ({inv.get('amount')} {inv.get('currency')})", "source": "ADOS (внутренние данные)", "confidence": "high"}
                )
        shipments = [
            s
            for s in active_only(bag["shipment"])
            if str(s.get("status")) in {"planned", "in_transit"} and not s.get("is_demo")
        ]
        for s in shipments[:3]:
            bullets["logistics"].append(
                {"text": f"Поставка: {s.get('title')} — статус {s.get('status')}", "source": "ADOS (внутренние данные)", "confidence": "high"}
            )
        tasks_today = [
            t for t in active_only(bag["task"])
            if str(t.get("due_at") or "")[:10] == today
            and str(t.get("status")) not in {"done", "cancelled"}
            and not t.get("is_demo")
        ]
        for t in tasks_today[:5]:
            bullets["today"].append({"text": f"Задача сегодня: {t.get('title')}", "source": "ADOS (внутренние данные)", "confidence": "high"})
        contracts = [
            c for c in active_only(bag["contract"])
            if c.get("end_at") and today <= str(c.get("end_at"))[:10] <= today[:8] + "31" and not c.get("is_demo")
        ]
        for c in contracts[:3]:
            bullets["risks"].append({"text": f"Договор истекает: {c.get('title')} ({str(c.get('end_at'))[:10]})", "source": "ADOS (внутренние данные)", "confidence": "high"})
        return bullets

    def _obs_bullets(self, observations: list[dict[str, Any]], sec_id: str, limit: int = 8) -> list[dict[str, Any]]:
        from services.agro_ops.analytics import is_metadata_observation

        items: list[dict[str, Any]] = []
        for obs in observations:
            if obs.get("record_kind") in {"provider_raw", "provider_snapshot"}:
                continue
            if sec_id not in (obs.get("sections") or ()):
                continue
            items.append(
                {
                    "text": obs.get("text"),
                    "summary": obs.get("notes") or obs.get("raw_value"),
                    "source": obs.get("source"),
                    "source_url": obs.get("source_url"),
                    "source_reference": obs.get("source_reference"),
                    "provider_id": obs.get("provider_id"),
                    "published_at": obs.get("published_at"),
                    "ingested_at": obs.get("ingested_at"),
                    "retrieved_at": obs.get("ingested_at"),
                    "confidence": obs.get("confidence"),
                    "observation_id": obs.get("id"),
                    "kind": "observation",
                    "canonical_type": obs.get("canonical_type"),
                    "metadata_only": is_metadata_observation(obs),
                    "value": obs.get("normalized_value"),
                    "unit": obs.get("unit"),
                }
            )
            if len(items) >= limit:
                break
        return items

    def _history_sufficient(self, observations: list[dict[str, Any]]) -> bool:
        dates = set()
        for obs in observations:
            raw = str(obs.get("published_at") or obs.get("ingested_at") or "")[:10]
            if len(raw) == 10:
                dates.add(raw)
        return len(dates) >= 7 or len(observations) >= 40

    def _provider_gaps(self, org: str) -> list[str]:
        from services.agro_ops.service import active_only

        bag = self._bag(org)  # type: ignore[attr-defined]
        gaps = []
        for src in active_only(bag.get("intel_source") or []):
            probe = str(src.get("probe_result") or src.get("connection_status") or "")
            if probe in {"FAILED", "BLOCKED", "UNAVAILABLE", "ERROR"}:
                gaps.append(f"{src.get('name') or src.get('provider_id')}: {src.get('note_ru') or probe}")
        return gaps[:12]

    def _build_report(self, org: str, kind: str) -> dict[str, Any]:
        from zoneinfo import ZoneInfo

        from services.agro_ops.analysts import calculate_chief_confidence, _freshness_score
        from services.agro_ops.analytics import is_numeric_observation
        from services.agro_ops.quality import PIPELINE_VERSION
        from services.agro_ops.service import active_only

        internal = self._internal_bullets(org)
        intel = [i for i in self._intel_items(org) if not i.get("is_demo") and str(i.get("data_class") or "") != "demo"]
        observations = [
            o
            for o in self._observation_items(org)
            if not o.get("is_demo")
            and str(o.get("data_class") or "") != "demo"
            and o.get("record_kind") not in {"provider_raw", "provider_snapshot"}
        ]
        numeric_obs = [o for o in observations if is_numeric_observation(o)]
        kyiv = datetime.now(ZoneInfo("Europe/Kyiv"))
        layout = MORNING_SECTIONS if kind in {"morning", "morning_on_demand", "weekly", "outlook"} else EVENING_SECTIONS
        if kind not in {"morning", "morning_on_demand", "evening", "weekly", "outlook"}:
            layout = REPORT_SECTIONS

        morning = None
        if kind == "evening":
            today = datetime.now(timezone.utc).date().isoformat()
            morning = next(
                (
                    r
                    for r in active_only(self._bag(org)["report"])  # type: ignore[attr-defined]
                    if r.get("record_type") == "report"
                    and r.get("report_kind") in {"morning", "morning_on_demand"}
                    and r.get("report_date") == today
                ),
                None,
            )
        morning_texts: set[str] = set()
        if morning:
            for sec in morning.get("sections") or []:
                for b in sec.get("bullets") or []:
                    if b.get("text"):
                        morning_texts.add(str(b["text"]))

        sections = []
        for sec_id, label in layout:
            items: list[dict[str, Any]] = []
            if sec_id in {"today", "watch", "tomorrow"}:
                items.extend(internal.get("today", [])[:5])
                items.extend(self._obs_bullets(observations, "trade", 2))
                items.extend(self._obs_bullets(observations, "ukraine", 2))
            elif sec_id in {"changed", "new_data"}:
                fresh = []
                for obs in observations:
                    row = {
                        "text": obs.get("text"),
                        "provider_id": obs.get("provider_id"),
                        "source_url": obs.get("source_url"),
                        "ingested_at": obs.get("ingested_at"),
                        "observation_id": obs.get("id"),
                        "marker": "NEW" if str(obs.get("text")) not in morning_texts else None,
                    }
                    if sec_id == "new_data" and row["marker"] != "NEW":
                        continue
                    if sec_id == "changed" and row["marker"] != "NEW":
                        continue
                    fresh.append(row)
                items = fresh[:8]
                if not items and sec_id == "changed":
                    items = [{"text": "С утра новых нормализованных наблюдений нет.", "source": "ADOS"}]
            else:
                items = [
                    {
                        "text": i.get("title"),
                        "summary": i.get("summary"),
                        "source": i.get("source"),
                        "source_url": i.get("source_url"),
                        "published_at": i.get("published_at"),
                        "confidence": i.get("confidence"),
                        "intel_id": i.get("id"),
                    }
                    for i in intel
                    if i.get("section") == sec_id
                ][:5]
                items.extend(self._obs_bullets(observations, sec_id))
                items.extend(internal.get(sec_id, [])[: max(0, 5 - len(items))])
            if kind == "evening":
                for b in items:
                    if b.get("text") and str(b["text"]) not in morning_texts and not b.get("marker"):
                        b["marker"] = "NEW"
            sections.append(
                {
                    "id": sec_id,
                    "label_ru": label,
                    "bullets": items,
                    "status": "DATA" if items else "NOT_CONFIGURED",
                    "note_ru": None if items else NOT_CONFIGURED_RU,
                }
            )

        # Keep 1.0 honesty: unused REPORT_SECTIONS without data stay listed internally
        for sec_id, label in REPORT_SECTIONS:
            if any(s["id"] == sec_id for s in sections):
                continue
            extra = self._obs_bullets(observations, sec_id)
            extra.extend([{"text": i.get("title"), "source": i.get("source")} for i in intel if i.get("section") == sec_id][:3])
            extra.extend(internal.get(sec_id, [])[:2])
            sections.append(
                {
                    "id": sec_id,
                    "label_ru": label,
                    "bullets": extra,
                    "status": "DATA" if extra else "NOT_CONFIGURED",
                    "note_ru": None if extra else NOT_CONFIGURED_RU,
                }
            )

        obs_count = len(observations)
        numeric_count = len(numeric_obs)
        provider_ids = sorted({str(o.get("provider_id")) for o in numeric_obs if o.get("provider_id")})
        gaps = self._provider_gaps(org)
        connected_n = len(provider_ids)
        coverage = min(1.0, connected_n / 6) if connected_n else 0.0
        page_ratio = (
            sum(1 for o in observations if o.get("source_reference") in {"html-title", "html-heading"} or o.get("canonical_type") == "page_signal") / obs_count
            if obs_count
            else 0.0
        )
        quality = min(1.0, connected_n / 4) * (0.45 if page_ratio >= 0.4 else 1.0)
        confidence = calculate_chief_confidence(
            coverage=coverage,
            freshness=_freshness_score(observations) * (0.7 if page_ratio >= 0.4 else 1.0),
            quality=quality,
            agreement=0.55 if page_ratio >= 0.4 else (1.0 if numeric_count else 0.2),
            missing_ratio=min(1.0, len(gaps) / 6),
        )
        metadata_n = sum(1 for o in observations if str(o.get("canonical_type")) == "page_signal" or str(o.get("source_reference") or "") in {"html-title", "html-heading"})
        if numeric_count:
            sources_note = (
                f"Использованы внутренние данные ADOS, ручной импорт и {connected_n} источников "
                f"с {numeric_count} числовыми наблюдениями. Цены, тонны и урожай не выдумываются."
            )
            if metadata_n >= max(1, int(obs_count * 0.5)):
                sources_note += " Часть наблюдений — метаданные источников, не живые рыночные ряды."
        elif obs_count:
            sources_note = (
                f"Источники отвечают ({obs_count} метаданных), но числовых рядов для этого обзора нет. "
                "Внешние котировки не выдумываются."
            )
        else:
            sources_note = (
                "Использованы только внутренние данные ADOS и вручную импортированные сообщения. "
                "Внешние источники не подключены."
            )
        titles = {
            "morning": "Утренний обзор",
            "morning_on_demand": "Утренний обзор (по запросу)",
            "evening": "Вечерний обзор",
            "weekly": "Недельный прогноз",
            "outlook": "Перспектива 1–2 месяца",
        }
        from services.agro_ops.presentation import business_report_sections

        result = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "record_type": "report",
            "report_kind": kind,
            "report_type": REPORT_TYPE_MAP.get(kind, kind.upper()),
            "title": titles.get(kind, kind),
            "summary": sources_note,
            "report_date": datetime.now(timezone.utc).date().isoformat(),
            "timezone": "Europe/Kyiv",
            "period_start": kyiv.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
            "period_end": kyiv.isoformat(),
            "generated_at": _now(),
            "generated_at_kyiv": kyiv.isoformat(),
            "sections": sections,
            "sections_json": sections,
            "observation_count": obs_count,
            "numeric_observation_count": numeric_count,
            "sources_count": connected_n,
            "source_count": connected_n,
            "pipeline_version": PIPELINE_VERSION,
            "confidence": confidence,
            "providers_json": provider_ids,
            "data_gaps_json": gaps,
            "data_gaps": gaps,
            "sources_note_ru": sources_note,
            "business_summary_ru": (
                f"Получены данные по {connected_n} источникам."
                if numeric_count
                else "Свежих числовых рядов для этого обзора нет."
            ),
            "is_latest": True,
            "version": 1,
            "status": "active",
            "created_at": _now(),
        }
        result["business_sections"] = business_report_sections(sections)
        return result

    async def generate_report(self, organization_id: str, kind: str, role: str | None = None, *, force: bool = False) -> dict[str, Any]:
        denied = require(role, "intel")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        if kind not in {"morning", "evening", "weekly", "outlook", "morning_on_demand"}:
            return {"ok": False, "error": "validation", "message_ru": "Доступны отчёты: morning, evening, weekly, outlook"}
        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        today = datetime.now(timezone.utc).date().isoformat()
        same_day = [
            r
            for r in active_only(self._bag(org)["report"])  # type: ignore[attr-defined]
            if r.get("record_type") == "report" and r.get("report_kind") == kind and r.get("report_date") == today
        ]
        existing = max(same_day, key=lambda r: str(r.get("generated_at") or "")) if same_day else None
        if existing and not force:
            return {"ok": True, "item": existing, "deduplicated": True}

        report = self._build_report(org, kind)
        report["version"] = len(same_day) + 1
        if report["version"] > 1:
            report["title"] = f"{report.get('title')} v{report['version']}"
        observations = self._observation_items(org)
        sufficient = self._history_sufficient(observations)
        if kind == "weekly":
            if not sufficient:
                report["themes"] = [
                    {
                        "theme": "Недостаточно истории",
                        "detail_ru": "Недостаточно накопленных данных для надёжного недельного прогноза.",
                        "confidence": "low",
                    }
                ]
                report["insufficient"] = True
            else:
                report["themes"] = self._weekly_themes(org)
        if kind == "outlook":
            report["scenarios"] = self._outlook_scenarios(org, sufficient=sufficient)
        latest_agents = next(
            (r for r in active_only(self._bag(org)["report"]) if r.get("record_type") == "agents_run"),  # type: ignore[attr-defined]
            None,
        )
        report["analyst_runs"] = [latest_agents["id"]] if latest_agents else []
        try:
            status = await self.providers_status(org, role)  # type: ignore[attr-defined]
            extra = self.explicit_data_gaps(org, status.get("items") or [], observations)  # type: ignore[attr-defined]
            merged = list(report.get("data_gaps") or [])
            for g in extra:
                if g not in merged:
                    merged.append(g)
            report["data_gaps"] = merged
            report["data_gaps_json"] = merged
        except Exception:
            pass
        saved = await self._persist("report", report)  # type: ignore[attr-defined]
        self._bag(org)["report"].insert(0, saved)  # type: ignore[attr-defined]
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org, entity_type="report", entity_id=saved["id"], action="created",
            summary=f"Сформирован отчёт: {saved.get('title')}", role=role,
        )
        await self._maybe_notify_on_create(org, "report", saved, role)  # type: ignore[attr-defined]
        return {"ok": True, "item": saved, "deduplicated": False}

    def _weekly_themes(self, org: str) -> list[dict[str, Any]]:
        intel = self._intel_items(org)
        observations = self._observation_items(org)
        themes = []
        if intel:
            themes.append(
                {
                    "theme": "Импортированные рыночные сообщения",
                    "detail_ru": f"За период вручную импортировано сообщений: {len(intel)}. Вероятностная оценка — по мере подключения источников.",
                    "confidence": "medium",
                }
            )
        if observations:
            themes.append(
                {
                    "theme": "Официальные наблюдения",
                    "detail_ru": (
                        f"Получено нормализованных записей: {len(observations)}. "
                        "Часто это метаданные каталогов, не ценовые ряды. Прогноз не выдумывается."
                    ),
                    "confidence": "low",
                }
            )
        else:
            themes.append(
                {
                    "theme": "Внешние рыночные данные",
                    "detail_ru": NOT_CONFIGURED_RU + ". Прогноз по ценам/урожаю станет доступен после подключения официальных источников.",
                    "confidence": "low",
                }
            )
        return themes

    def _outlook_scenarios(self, org: str, *, sufficient: bool = False) -> list[dict[str, Any]]:
        if not sufficient:
            note = (
                "Недостаточно накопленных данных (история рынка/производства/торговли/погоды) "
                "для надёжной перспективы на 1–2 месяца. Сценарий не выдумывается."
            )
            return [
                {"id": "base", "label_ru": "Базовый сценарий", "confidence": "low", "conditions_ru": note,
                 "triggers_ru": "Нужна накопленная история официальных наблюдений"},
                {"id": "positive", "label_ru": "Позитивный сценарий", "confidence": "low", "conditions_ru": note,
                 "triggers_ru": "Недостаточно данных"},
                {"id": "negative", "label_ru": "Негативный сценарий", "confidence": "low", "conditions_ru": note,
                 "triggers_ru": "Недостаточно данных"},
            ]
        base_note = (
            "Сценарий не является гарантированным прогнозом. Условия описаны качественно "
            "по накопленным официальным наблюдениям и внутренним данным ADOS."
        )
        return [
            {"id": "base", "label_ru": "Базовый сценарий", "confidence": "low", "conditions_ru": base_note,
             "triggers_ru": "Стабильные официальные публикации и внутренняя операционка"},
            {"id": "positive", "label_ru": "Позитивный сценарий", "confidence": "low", "conditions_ru": base_note,
             "triggers_ru": "Рост спроса на рынках сбыта, стабильная логистика"},
            {"id": "negative", "label_ru": "Негативный сценарий", "confidence": "low", "conditions_ru": base_note,
             "triggers_ru": "Погодные риски, логистические ограничения, снижение цен"},
        ]

    async def list_reports(
        self, organization_id: str, role: str | None = None, kind: str | None = None, query: dict[str, str] | None = None
    ) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        items = [r for r in active_only(self._bag(org)["report"]) if r.get("record_type") == "report"]  # type: ignore[attr-defined]
        if kind:
            items = [r for r in items if r.get("report_kind") == kind]
        today = str(query.get("today") or "").strip() if query else ""
        if today in {"1", "true", "yes"}:
            day = datetime.now(timezone.utc).date().isoformat()
            items = [r for r in items if r.get("report_date") == day]
        self._annotate_report_versions(items)
        return {"ok": True, "items": items}

    def _annotate_report_versions(self, items: list[dict[str, Any]]) -> None:
        groups: dict[tuple[Any, Any], list[dict[str, Any]]] = {}
        for row in items:
            key = (row.get("report_kind"), row.get("report_date"))
            groups.setdefault(key, []).append(row)
        for group in groups.values():
            ordered = sorted(group, key=lambda r: str(r.get("generated_at") or ""))
            for idx, row in enumerate(ordered, 1):
                row["version"] = int(row.get("version") or idx)
        by_kind: dict[Any, list[dict[str, Any]]] = {}
        for row in items:
            by_kind.setdefault(row.get("report_kind"), []).append(row)
        for group in by_kind.values():
            ordered = sorted(group, key=lambda r: str(r.get("generated_at") or ""))
            latest = ordered[-1] if ordered else None
            for row in ordered:
                row["is_latest"] = row is latest
                row["latest_badge_ru"] = "АКТУАЛЬНЫЙ" if row["is_latest"] else "УСТАРЕЛ"

    async def get_report(self, organization_id: str, report_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        listed = await self.list_reports(organization_id, role)
        item = next((r for r in listed.get("items") or [] if str(r.get("id")) == str(report_id)), None)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Обзор не найден"}
        return {"ok": True, "item": item}

    async def latest_or_generate(self, organization_id: str, kind: str, role: str | None = None, *, generate: bool = False) -> dict[str, Any]:
        listed = await self.list_reports(organization_id, role, kind)
        today = datetime.now(timezone.utc).date().isoformat()
        todays = [r for r in listed.get("items") or [] if r.get("report_date") == today]
        latest = next((r for r in todays if r.get("is_latest")), None) or (todays[0] if todays else None)
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        observations = self._observation_items(org)
        from services.agro_ops.analytics import is_numeric_observation

        numeric_n = sum(1 for o in observations if is_numeric_observation(o) and not o.get("is_demo"))
        stale_empty = bool(latest) and int(latest.get("sources_count") or 0) == 0 and numeric_n > 0
        if stale_empty:
            return await self.generate_report(organization_id, kind, role, force=True)
        if latest and not generate:
            return {
                "ok": True,
                "item": latest,
                "opened": True,
                "offer_generate": False,
                "stale": False,
                "offer_recalculate": False,
                "message_ru": None,
            }
        if not generate and kind in {"morning", "evening"}:
            return {"ok": True, "item": None, "opened": False, "offer_generate": True, "message_ru": "Обзора за сегодня нет. Сформировать сейчас?"}
        return await self.generate_report(organization_id, kind, role, force=bool(generate))

    async def run_report_sweep(self, organization_id: str | None = None, kind: str | None = None) -> dict[str, Any]:
        """Scheduler entrypoint — idempotent per (org, kind, date)."""
        hour = datetime.now(timezone.utc).hour
        kind = kind or ("morning" if hour < 12 else "evening")
        orgs = [organization_id] if organization_id else list(self._mem.keys())  # type: ignore[attr-defined]
        generated = []
        for org in orgs:
            if not org:
                continue
            try:
                analysis_type = "morning" if kind in {"morning", "morning_on_demand"} else "evening"
                await self.run_analysis(org, {"analysis_type": analysis_type}, role="platform_owner")  # type: ignore[attr-defined]
            except Exception:
                pass
            res = await self.generate_report(org, kind, role="platform_owner")
            if res.get("ok") and not res.get("deduplicated"):
                generated.append(org)
        return {"ok": True, "kind": kind, "generated_for": generated, "orgs_checked": len(orgs)}

    # ------------------------------------------------------------------
    # ask AI about a card (contextual explanation, honest)
    # ------------------------------------------------------------------

    async def ask_ai(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "ai")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        question = str(body.get("question") or "").strip()
        if not question:
            return {"ok": False, "error": "validation", "message_ru": "Задайте вопрос"}
        context = body.get("context") or {}
        observations = self._observation_items(org)
        if observations:
            answer = (
                "Ответ подготовлен по контексту карточки, внутренним данным ADOS и нормализованным наблюдениям. "
                "Котировки и тонны не выдумываются (DATA GAP, если в наблюдении нет экономического ряда). "
                f"Вопрос: «{question}». Контекст: {str(context)[:400] or 'не передан'}."
            )
            gaps = ["Экономический ряд может отсутствовать — проверьте тип наблюдения"]
        else:
            answer = (
                "Ответ подготовлен только по переданному контексту карточки и внутренним данным ADOS. "
                "Внешние рыночные источники не подключены, поэтому котировки, урожай и госданные не приводятся (DATA GAP). "
                f"Вопрос: «{question}». Контекст: {str(context)[:400] or 'не передан'}."
            )
            gaps = ["Внешние источники не подключены"]
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "record_type": "ai_answer",
            "question": question,
            "answer_ru": answer,
            "context": context,
            "data_gaps": gaps,
            "status": "active",
            "created_at": _now(),
        }
        saved = await self._persist("report", item)  # type: ignore[attr-defined]
        self._bag(org)["report"].insert(0, saved)  # type: ignore[attr-defined]
        return {"ok": True, "item": saved}
