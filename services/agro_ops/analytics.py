"""AGRO 1.5 — stored AnalysisRun, freshness, gaps, custom query, change detection."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from services.agro_ops.rbac import require

ANALYSIS_TYPES = {
    "operational": "Оперативный анализ",
    "morning": "Утренний анализ",
    "evening": "Вечерний анализ",
    "weekly": "Недельный анализ",
    "outlook": "Стратегический прогноз 1–2 месяца",
    "custom": "Пользовательский анализ",
}

FRESHNESS_LABELS = {
    "ua_customs_open_data": "Таможня",
    "usda_wasde": "USDA",
    "fao": "FAO",
    "eurostat": "Eurostat",
    "ua_hydromet": "Укргидромет",
    "weather_provider": "Open-Meteo",
    "ec_agri": "EU Crops",
    "amis": "AMIS",
    "world_bank": "World Bank",
    "ua_stat": "Госстат",
    "fx_rates": "НБУ",
}

CROP_ALIASES = {
    "пшениц": "Пшеница",
    "wheat": "Пшеница",
    "кукуруз": "Кукуруза",
    "corn": "Кукуруза",
    "ячмен": "Ячмень",
    "подсолнеч": "Подсолнечник",
    "рапс": "Рапс",
    "соя": "Соя",
}

MONTHS_RU = (
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
)

INSUFFICIENT_RU = "Недостаточно данных"

SECTION_ORDER = [
    ("chief", "Главное заключение"),
    ("changed", "Что изменилось"),
    ("risks", "Риски"),
    ("opportunities", "Возможности"),
    ("prices", "Цены и рынки"),
    ("trade", "Экспорт / импорт"),
    ("weather", "Погода"),
    ("harvest", "Урожай"),
    ("logistics", "Логистика"),
    ("world", "Мировые рынки"),
    ("consensus", "Консенсус аналитиков"),
    ("sources", "Источники"),
    ("gaps", "Пробелы данных"),
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _kyiv_now() -> datetime:
    return datetime.now(ZoneInfo("Europe/Kyiv"))


def human_datetime_ru(value: str | None) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "—"
    try:
        ts = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(ZoneInfo("Europe/Kyiv"))
    except Exception:
        return raw.replace("T", " ")[:16]
    return f"{ts.day} {MONTHS_RU[ts.month - 1]}, {ts.strftime('%H:%M')}"


def _ru_num(n: int, one: str, few: str, many: str) -> str:
    n = max(0, int(n))
    n10, n100 = n % 10, n % 100
    if n10 == 1 and n100 != 11:
        return f"{n} {one}"
    if 2 <= n10 <= 4 and not 12 <= n100 <= 14:
        return f"{n} {few}"
    return f"{n} {many}"


def format_age_ru(iso: str | None) -> str | None:
    if not iso:
        return None
    try:
        ts = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        hours = max(0.0, (datetime.now(timezone.utc) - ts.astimezone(timezone.utc)).total_seconds() / 3600)
    except Exception:
        return None
    if hours < 1:
        return "менее часа"
    if hours < 24:
        return _ru_num(round(hours), "час", "часа", "часов")
    return _ru_num(round(hours / 24), "день", "дня", "дней")


def is_numeric_observation(obs: dict[str, Any]) -> bool:
    if obs.get("is_demo") or str(obs.get("data_class") or "") == "demo":
        return False
    if str(obs.get("data_class") or "") == "manual":
        try:
            return obs.get("normalized_value") not in (None, "") or float(obs.get("price") or obs.get("value") or 0) != 0
        except (TypeError, ValueError):
            return False
    value = obs.get("normalized_value")
    if value in (None, "", "null"):
        return False
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def is_metadata_observation(obs: dict[str, Any]) -> bool:
    if str(obs.get("data_class") or "") in {"numeric", "manual"}:
        return False
    if is_numeric_observation(obs):
        return False
    ref = str(obs.get("source_reference") or "")
    ctype = str(obs.get("canonical_type") or "")
    if ctype == "page_signal" or ref in {"html-title", "html-heading", "ckan-title", "catalog", "eurostat-toc"}:
        return True
    return obs.get("normalized_value") in (None, "", "null")


def detect_crop(text: str) -> str | None:
    low = (text or "").lower()
    for key, name in CROP_ALIASES.items():
        if key in low:
            return name
    return None


class AgroOpsAnalyticsMixin:
    """Mixed into AgroOpsService — AnalysisRun persistence and dashboard."""

    def _analysis_runs(self, org: str) -> list[dict[str, Any]]:
        from services.agro_ops.service import active_only

        return [r for r in active_only(self._bag(org)["report"]) if r.get("record_type") == "analysis_run"]  # type: ignore[attr-defined]

    def _filter_observations(
        self, observations: list[dict[str, Any]], body: dict[str, Any]
    ) -> list[dict[str, Any]]:
        crop = str(body.get("crop") or "").strip()
        country = str(body.get("country") or "").strip().lower()
        region = str(body.get("region") or "").strip().lower()
        source = str(body.get("source") or body.get("provider_id") or "").strip()
        period = str(body.get("period") or "").strip()
        question = str(body.get("question") or body.get("query") or "").strip()
        if not crop and question:
            crop = detect_crop(question) or ""
        out = observations
        if crop:
            low = crop.lower()
            out = [
                o
                for o in out
                if low in str(o.get("text") or o.get("title") or "").lower() or low in str(o.get("commodity") or "").lower()
            ]
        if country:
            out = [o for o in out if country in str(o.get("country") or o.get("region") or o.get("text") or "").lower()] or out
        if region:
            out = [o for o in out if region in str(o.get("region") or o.get("text") or "").lower()] or out
        if source:
            out = [o for o in out if source in {str(o.get("provider_id") or ""), str(o.get("source") or "")}] or out
        if len(period) >= 10:
            out = [o for o in out if str(o.get("published_at") or o.get("ingested_at") or "")[:10] >= period[:10]] or out
        return out

    def provider_freshness_board(
        self, providers: list[dict[str, Any]], observations: list[dict[str, Any]] | None = None
    ) -> list[dict[str, Any]]:
        latest_by_pid: dict[str, str] = {}
        numeric_by_pid: dict[str, int] = {}
        for obs in observations or []:
            pid = str(obs.get("provider_id") or "")
            if not pid:
                continue
            if is_numeric_observation(obs):
                numeric_by_pid[pid] = numeric_by_pid.get(pid, 0) + 1
            ts = str(obs.get("ingested_at") or obs.get("observed_at") or obs.get("published_at") or "")
            if ts and (pid not in latest_by_pid or ts > latest_by_pid[pid]):
                latest_by_pid[pid] = ts
        board = []
        for p in providers:
            pid = str(p.get("id") or p.get("provider_id") or "")
            if pid in {"manual_import"}:
                continue
            health = str(p.get("health_state") or p.get("connection_status") or "")
            numeric_n = int(p.get("numeric_count") or numeric_by_pid.get(pid) or 0)
            last = p.get("last_success_at") or latest_by_pid.get(pid)
            age = format_age_ru(str(last) if last else None)
            live_claim = bool(last) and health == "CONNECTED" and age == "менее часа"
            if health in {"NOT_CONFIGURED", "REQUIRES_CONFIGURATION", "NEEDS_KEY"} and numeric_n == 0:
                age_ru = "нет данных"
                live_claim = False
            elif last and age:
                age_ru = age
            elif numeric_n > 0 or health in {"CONNECTED", "PARTIAL", "DEGRADED", "STALE"}:
                age_ru = "есть числовые данные" if numeric_n else "есть ответ источника"
            else:
                age_ru = "нет данных"
            board.append(
                {
                    "provider_id": pid,
                    "label_ru": FRESHNESS_LABELS.get(pid) or p.get("label_ru") or pid,
                    "age_ru": age_ru,
                    "last_success_at": last,
                    "health_state": health,
                    "health_color": p.get("health_color") or "",
                    "live": live_claim,
                    "records": int(p.get("observation_count") or 0),
                    "numeric_count": numeric_n,
                }
            )
        return board

    def explicit_data_gaps(
        self, org: str, providers: list[dict[str, Any]], observations: list[dict[str, Any]]
    ) -> list[str]:
        return [g["text"] for g in self.structured_data_gaps(org, providers, observations)]

    def structured_data_gaps(
        self, org: str, providers: list[dict[str, Any]], observations: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        from services.agro_ops.engines import structured_data_gaps
        from services.agro_ops.service import active_only

        trips = active_only(self._bag(org).get("trip") or [])  # type: ignore[attr-defined]
        quotes = active_only(self._bag(org).get("market_price") or [])  # type: ignore[attr-defined]
        return structured_data_gaps(org, providers, observations, trips=trips, quotes=quotes)

    def build_chart_series(self, observations: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        buckets: dict[str, list[dict[str, Any]]] = {
            "price": [],
            "production": [],
            "yield_or_area": [],
            "trade": [],
            "fx": [],
            "weather": [],
        }
        kind_map = {
            "price": "price",
            "production": "production",
            "yield": "yield_or_area",
            "area": "yield_or_area",
            "trade": "trade",
            "fx": "fx",
            "weather": "weather",
        }
        for obs in observations:
            if not is_numeric_observation(obs) or str(obs.get("data_class") or "") == "demo":
                continue
            kind = kind_map.get(str(obs.get("series_kind") or ""), "")
            if not kind:
                continue
            buckets[kind].append(
                {
                    "t": obs.get("observed_at") or obs.get("published_at"),
                    "v": obs.get("normalized_value"),
                    "unit": obs.get("unit"),
                    "source": obs.get("provider_id"),
                    "source_url": obs.get("source_url"),
                    "series_id": obs.get("series_id"),
                    "commodity": obs.get("commodity"),
                    "title": obs.get("text") or obs.get("title"),
                    "data_class": obs.get("data_class") or "numeric",
                }
            )
        for key, rows in buckets.items():
            rows.sort(key=lambda r: str(r.get("t") or ""))
            latest_by_source: dict[str, dict[str, Any]] = {}
            for row in rows:
                latest_by_source[str(row.get("source") or row.get("series_id") or "")] = row
            tail = rows[-24:]
            for row in latest_by_source.values():
                if row not in tail:
                    tail.append(row)
            tail.sort(key=lambda r: str(r.get("t") or ""))
            buckets[key] = tail[-36:]
        from services.agro_ops.quality import sanitize_chart_series

        return sanitize_chart_series(buckets)

    def _manual_price_observations(self, org: str) -> list[dict[str, Any]]:
        from services.agro_ops.service import active_only

        out: list[dict[str, Any]] = []
        for p in active_only(self._bag(org).get("market_price") or []):  # type: ignore[attr-defined]
            if p.get("is_demo") or str(p.get("data_class") or "") == "demo":
                continue
            try:
                value = float(p.get("price"))
            except (TypeError, ValueError):
                continue
            kind_label = str(p.get("price_kind") or "local_price")
            out.append(
                {
                    **p,
                    "record_kind": "market_price",
                    "provider_id": "manual_import",
                    "sections": ("prices", "ukraine"),
                    "text": f"MANUAL DATA · {kind_label}: {p.get('commodity') or p.get('crop')} {value} {p.get('currency') or ''} / {p.get('unit') or 'т'}",
                    "title": f"MANUAL DATA · {p.get('commodity') or 'цена'} {value}",
                    "normalized_value": value,
                    "value": value,
                    "data_class": "manual",
                    "manual_status": str(p.get("manual_status") or "CONFIRMED").upper(),
                    "market_usable": str(p.get("manual_status") or "CONFIRMED").upper() == "CONFIRMED",
                    "series_kind": "freight" if str(p.get("price_kind") or "") == "freight" else "price",
                    "series_id": (
                        f"manual:{kind_label}:{p.get('commodity') or p.get('crop') or 'x'}:"
                        f"{p.get('unit') or 't'}:{p.get('currency') or ''}"
                    ),
                    "observed_at": p.get("valid_from") or p.get("date") or p.get("created_at"),
                    "source": "MANUAL DATA",
                    "canonical_type": "AgroPriceObservation",
                }
            )
        return out

    def _category_block(
        self, observations: list[dict[str, Any]], sec_id: str, *, economic: bool
    ) -> dict[str, Any]:
        items = [o for o in observations if sec_id in (o.get("sections") or ())]
        if not items:
            return {"id": sec_id, "status": "INSUFFICIENT", "note_ru": INSUFFICIENT_RU, "bullets": []}
        bullets = [
            {
                "text": o.get("text"),
                "source": o.get("provider_id") or o.get("source"),
                "source_url": o.get("source_url"),
                "observation_id": o.get("id"),
                "published_at": o.get("published_at"),
                "retrieved_at": o.get("ingested_at"),
                "metadata_only": is_metadata_observation(o),
                "manual": str(o.get("data_class") or "") == "manual",
                "value": o.get("normalized_value"),
                "unit": o.get("unit"),
                "source_url": o.get("source_url"),
                "crop": detect_crop(str(o.get("text") or "")),
            }
            for o in items[:8]
        ]
        note = None
        if not economic or all(b.get("metadata_only") for b in bullets):
            note = "Это метаданные источника, не рыночное наблюдение. Вывод по ценам/тоннам не формируется."
        return {"id": sec_id, "status": "DATA", "note_ru": note, "bullets": bullets}

    def _what_changed(self, prev: dict[str, Any] | None, current: dict[str, Any]) -> list[dict[str, Any]]:
        if not prev:
            return []
        rows: list[dict[str, Any]] = []
        prev_src = set(prev.get("providers_json") or prev.get("input_provider_ids") or [])
        cur_src = set(current.get("providers_json") or [])
        for sid in sorted(cur_src - prev_src):
            rows.append({"marker": "NEW", "text": f"новый источник: {sid}"})
        prev_risks = {str(x) for x in (prev.get("risks") or [])}
        for risk in current.get("risks") or []:
            if str(risk) not in prev_risks:
                rows.append({"marker": "⚠", "text": f"новый риск: {risk}"})
        prev_ops = {str(x) for x in (prev.get("opportunities") or [])}
        for opp in current.get("opportunities") or []:
            if str(opp) not in prev_ops:
                rows.append({"marker": "★", "text": f"новая возможность: {opp}"})
        return rows[:12]

    def _iso_dt(self, raw: Any) -> datetime | None:
        text = str(raw or "").strip()
        if not text:
            return None
        try:
            ts = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return ts.astimezone(timezone.utc)
        except Exception:
            return None

    def build_coverage_card(
        self,
        providers: list[dict[str, Any]],
        observations: list[dict[str, Any]],
        gaps: list[str],
        latest: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        real = [
            o
            for o in observations
            if str(o.get("data_class") or "") != "demo" and not o.get("is_demo")
        ]
        numeric = [o for o in real if is_numeric_observation(o)]
        metadata = [o for o in real if is_metadata_observation(o)]
        connected = [
            p
            for p in providers
            if str(p.get("health_state") or p.get("connection_status") or "") == "CONNECTED"
            and int(p.get("numeric_count") or 0) > 0
        ]
        if not connected:
            pids = {str(o.get("provider_id")) for o in numeric if o.get("provider_id")}
            connected = [{"id": pid} for pid in sorted(pids)]
        cutoff = datetime.now(timezone.utc).timestamp() - 24 * 3600
        last_24h = 0
        for obs in numeric:
            ts = self._iso_dt(obs.get("observed_at") or obs.get("ingested_at") or obs.get("published_at"))
            if ts and ts.timestamp() >= cutoff:
                last_24h += 1
        series = self.build_chart_series(real)
        required = ("price", "production", "yield_or_area", "trade", "fx", "weather")
        present = sum(1 for key in required if series.get(key))
        coverage_pct = int(round(100 * present / len(required))) if required else 0
        chief = (latest or {}).get("chief") if isinstance((latest or {}).get("chief"), dict) else {}
        try:
            confidence_pct = int(chief.get("confidence") if chief.get("confidence") is not None else (latest or {}).get("confidence") or coverage_pct)
        except (TypeError, ValueError):
            confidence_pct = coverage_pct
        unresolved = 0
        for g in gaps or []:
            if isinstance(g, dict):
                if str(g.get("severity") or "") in {"CRITICAL", "IMPORTANT"}:
                    unresolved += 1
            else:
                unresolved += 1
        return {
            "connected_sources": len(connected),
            "numeric_observations": len(numeric),
            "metadata_observations": len(metadata),
            "observations_last_24h": last_24h,
            "coverage_pct": coverage_pct,
            "confidence_pct": confidence_pct,
            "unresolved_gaps": unresolved,
        }

    async def analytics_dashboard(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.quality import (
            PIPELINE_VERSION,
            detect_anomalies,
            operational_counts,
            provider_health_summary,
            validate_observations,
        )
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        status = await self.providers_status(org, role)  # type: ignore[attr-defined]
        providers = status.get("items") or []
        observations = [
            o
            for o in self._observation_items(org)  # type: ignore[attr-defined]
            if o.get("record_kind") not in {"provider_raw", "provider_snapshot"}
            and str(o.get("data_class") or "") != "demo"
            and not o.get("is_demo")
        ]
        trips = active_only(self._bag(org).get("trip") or [])  # type: ignore[attr-defined]
        market_prices = active_only(self._bag(org).get("market_price") or [])  # type: ignore[attr-defined]
        numeric_n = sum(1 for o in observations if is_numeric_observation(o))
        meta_n = sum(1 for o in observations if is_metadata_observation(o))
        runs = self._analysis_runs(org)
        latest = runs[0] if runs else None
        gaps_structured = self.structured_data_gaps(org, providers, observations)
        gaps = [g["text"] for g in gaps_structured]
        coverage = self.build_coverage_card(providers, observations, gaps_structured, latest)
        demo_loaded = any(s.get("demo_loaded") for s in active_only(self._bag(org).get("settings") or []))  # type: ignore[attr-defined]
        refresh_meta = self._refresh_meta_row(org)  # type: ignore[attr-defined]
        quality_obs = list(observations) + self._manual_price_observations(org)
        source_health = provider_health_summary(
            providers,
            last_full_refresh_at=(refresh_meta or {}).get("last_full_refresh_at"),
            last_full_refresh_duration_sec=(refresh_meta or {}).get("last_full_refresh_duration_sec"),
        )
        counts = operational_counts(observations, trips=trips, market_prices=market_prices)
        quality_flags = validate_observations(quality_obs)
        anomalies = detect_anomalies(quality_obs)
        from services.agro_ops.presentation import business_brief, opportunity_cards, risk_cards, strip_tech_from_provider, what_changed_24h

        brief = business_brief(providers, quality_obs)
        return {
            "ok": True,
            "pipeline_version": PIPELINE_VERSION,
            "source_health": source_health,
            "operational_counts": counts,
            "quality_flags": quality_flags,
            "anomalies": anomalies,
            "business_brief": brief,
            "risk_cards": risk_cards(quality_obs, providers, trips),
            "opportunity_cards": opportunity_cards(quality_obs, trips),
            "what_changed": what_changed_24h(quality_obs),
            "providers_business": [strip_tech_from_provider(p) for p in providers],
            "freshness": self.provider_freshness_board(providers, observations),
            "gaps": gaps,
            "gaps_structured": gaps_structured,
            "coverage": coverage,
            "connected_sources": coverage["connected_sources"],
            "numeric_observation_count": numeric_n,
            "metadata_observation_count": meta_n,
            "observations_last_24h": coverage["observations_last_24h"],
            "coverage_pct": coverage["coverage_pct"],
            "confidence_pct": coverage["confidence_pct"],
            "unresolved_gaps": coverage["unresolved_gaps"],
            "demo_mode": bool(demo_loaded),
            "observation_count": len(observations),
            "series": self.build_chart_series(observations),
            "providers_available": len(
                [p for p in providers if str(p.get("health_state")) in {"CONNECTED", "PARTIAL", "DEGRADED", "STALE"}]
            ),
            "latest": latest,
            "analysis_types": [{"id": k, "label_ru": v} for k, v in ANALYSIS_TYPES.items()],
        }

    async def run_analysis(self, organization_id: str, body: dict[str, Any] | None = None, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "ai")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        body = dict(body or {})
        analysis_type = str(body.get("analysis_type") or body.get("kind") or "operational")
        if analysis_type not in ANALYSIS_TYPES:
            analysis_type = "operational"
        question = str(body.get("question") or body.get("query") or "").strip()
        if analysis_type == "custom" and not question:
            return {"ok": False, "error": "validation", "message_ru": "Укажите, что нужно проанализировать"}

        status = await self.providers_status(org, role)  # type: ignore[attr-defined]
        providers = status.get("items") or []
        observations = [o for o in self._observation_items(org) if o.get("record_kind") not in {"provider_raw", "provider_snapshot"}]  # type: ignore[attr-defined]
        observations = [
            o
            for o in observations
            if str(o.get("data_class") or "") != "demo" and not o.get("is_demo")
        ]
        observations.extend(self._manual_price_observations(org))
        observations = self._filter_observations(observations, body)
        from services.agro_ops.quality import PIPELINE_VERSION, detect_anomalies, validate_observations

        quality_flags = validate_observations(observations)
        anomalies = detect_anomalies(observations)
        internal = self._internal_bullets(org)  # type: ignore[attr-defined]
        from services.agro_ops.engines import build_logistics_status, production_observations
        from services.agro_ops.service import active_only as _active

        economic_obs = production_observations(observations)
        economic = bool(economic_obs)
        metadata_only = bool(observations) and not economic

        agent_body = {**body, "_filtered_observations": observations}
        agents_res = await self.run_agents(organization_id, agent_body, role)  # type: ignore[attr-defined]
        if not agents_res.get("ok"):
            return agents_res
        agents = agents_res["item"]
        chief = dict(agents.get("chief") or {})
        specialists = [a for a in (agents.get("agents") or []) if a.get("findings")]
        gaps_structured = self.structured_data_gaps(org, providers, observations)
        gaps = [g["text"] for g in gaps_structured]
        if chief.get("data_gaps"):
            for g in chief["data_gaps"]:
                if g not in gaps:
                    gaps.append(str(g))

        kyiv = _kyiv_now()
        title = ANALYSIS_TYPES[analysis_type]
        if question:
            title = f"{title}: {question[:80]}"
        topic = detect_crop(question) or body.get("crop") or "Общий рынок"
        provider_ids = sorted(
            {
                str(o.get("provider_id"))
                for o in economic_obs
                if o.get("provider_id")
            }
        )
        engine_risks = [r for r in (chief.get("risks") or []) if isinstance(r, dict)]
        risks = list(engine_risks)
        for x in internal.get("risks") or []:
            risks.append({"text": x.get("text"), "source": "ADOS", "level": "HIGH", "reason": "internal ADOS", "sources": []})
        opportunities = [o for o in (chief.get("opportunities") or []) if isinstance(o, dict)]
        trips = _active(self._bag(org).get("trip") or [])  # type: ignore[attr-defined]
        quotes = _active(self._bag(org).get("market_price") or [])  # type: ignore[attr-defined]
        logistics = chief.get("logistics") or build_logistics_status(observations, trips, providers, quotes=quotes)
        if metadata_only:
            chief_note = (
                "Источники отвечают, но в нормализованном слое только метаданные каталогов и страниц. "
                "Экономический вывод (цены, тонны, урожай) не выдумывается."
            )
        elif not observations:
            chief_note = "Нормализованных внешних наблюдений нет. Используются только внутренние данные ADOS."
        else:
            chief_note = str(chief.get("note_ru") or "")
        if economic:
            chief_note = (
                (chief_note + " ") if chief_note else ""
            ) + "В выводе использованы только числовые ряды официальных API и явно помеченные MANUAL DATA. DEMO исключён."

        series = self.build_chart_series(observations)
        sections = {
            "chief": {
                "bias": chief.get("bias") or "WATCH",
                "conclusion_ru": chief_note,
                "confidence": chief.get("confidence"),
                "key_drivers": chief.get("key_drivers") or [],
            },
            "ukraine": self._category_block(observations, "ukraine", economic=economic),
            "prices": self._category_block(observations, "prices", economic=economic),
            "harvest": self._category_block(observations, "harvest", economic=economic),
            "trade": self._category_block(observations, "trade", economic=economic),
            "weather": self._category_block(observations, "weather", economic=economic),
            "logistics": {
                "id": "logistics",
                "status": "DATA" if logistics.get("commercial_rate") or logistics.get("findings") else "INSUFFICIENT",
                "note_ru": None if logistics.get("findings") else INSUFFICIENT_RU,
                "bullets": [
                    {"text": f.get("text"), "source": f.get("source") or "ADOS", "sources": f.get("sources") or [], "metadata_only": f.get("metadata_only")}
                    for f in (logistics.get("findings") or [])[:8]
                ],
                "status_ru": logistics.get("status_ru"),
                "rate_change_pct": logistics.get("rate_change_pct"),
                "route_pressure_ru": logistics.get("route_pressure_ru"),
                "cheapest_route": logistics.get("cheapest_route"),
                "expensive_routes": logistics.get("expensive_routes"),
                "risk_ru": logistics.get("risk_ru"),
                "recommended_checks": logistics.get("recommended_checks") or [],
            },
            "world": self._category_block(observations, "world", economic=economic),
        }
        if internal.get("logistics"):
            extra = [{"text": b.get("text"), "source": "ADOS", "metadata_only": False} for b in internal["logistics"][:5]]
            sections["logistics"]["bullets"] = extra + list(sections["logistics"].get("bullets") or [])
            sections["logistics"]["status"] = "DATA"
            sections["logistics"]["note_ru"] = None

        prev = next((r for r in self._analysis_runs(org) if r.get("analysis_type") == analysis_type), None)
        current_cmp = {"providers_json": provider_ids, "risks": risks, "opportunities": opportunities}
        changed = self._what_changed(prev, current_cmp)

        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "record_type": "analysis_run",
            "analysis_type": analysis_type,
            "title": title,
            "title_ru": title,
            "topic_ru": topic,
            "question": question or None,
            "period_start": kyiv.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
            "period_end": kyiv.isoformat(),
            "generated_at": _now(),
            "generated_at_kyiv": kyiv.isoformat(),
            "generated_at_human": human_datetime_ru(kyiv.isoformat()),
            "timezone": "Europe/Kyiv",
            "agents_run_id": agents.get("id"),
            "specialists_executed": agents.get("specialists_executed") or [],
            "specialists_with_data": [a.get("agent") for a in specialists],
            "chief": {**chief, "note_ru": chief_note, "metadata_only": metadata_only, "economic_data": economic},
            "confidence": chief.get("confidence"),
            "bias": chief.get("bias") or "WATCH",
            "key_factors": chief.get("key_drivers") or [],
            "what_changed": changed,
            "risks": [
                {
                    "text": r.get("text"),
                    "level": r.get("level") or "MEDIUM",
                    "reason": r.get("reason"),
                    "source": r.get("source") or "ADOS",
                    "sources": r.get("sources") or [],
                }
                for r in risks[:12]
                if isinstance(r, dict)
            ],
            "opportunities": opportunities[:8],
            "logistics": logistics,
            "data_gaps_structured": gaps_structured,
            "what_to_watch": chief.get("what_to_watch") or [],
            "sections": sections,
            "consensus": [
                {
                    "agent": a.get("agent"),
                    "label_ru": a.get("label_ru"),
                    "conclusion": a.get("conclusion"),
                    "confidence": a.get("confidence"),
                    "data_gaps": a.get("data_gaps") or [],
                }
                for a in (agents.get("agents") or [])
            ],
            "sources": [
                {
                    "provider_id": pid,
                    "label_ru": FRESHNESS_LABELS.get(pid) or pid,
                    "records": [o for o in observations if str(o.get("provider_id")) == pid][:5],
                }
                for pid in provider_ids
            ],
            "providers_json": provider_ids,
            "sources_count": len(provider_ids),
            "source_count": len(provider_ids),
            "pipeline_version": PIPELINE_VERSION,
            "quality_flags": quality_flags,
            "anomalies": anomalies,
            "observation_count": len(observations),
            "numeric_observation_count": sum(1 for o in observations if is_numeric_observation(o)),
            "metadata_observation_count": sum(1 for o in observations if is_metadata_observation(o)),
            "series": series,
            "data_gaps": gaps,
            "data_gaps_json": gaps,
            "freshness": self.provider_freshness_board(providers, observations),
            "filters": {
                "crop": body.get("crop"),
                "country": body.get("country"),
                "region": body.get("region"),
                "period": body.get("period"),
                "source": body.get("source"),
            },
            "status": "active",
            "created_at": _now(),
        }
        saved = await self._persist("report", item)  # type: ignore[attr-defined]
        self._bag(org)["report"].insert(0, saved)  # type: ignore[attr-defined]
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org, entity_type="analysis_run", entity_id=saved["id"], action="created",
            summary=f"Анализ: {title}", role=role,
        )
        return {"ok": True, "item": saved}

    async def list_analyses(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        items = self._analysis_runs(org)
        for row in items:
            row.setdefault("generated_at_human", human_datetime_ru(str(row.get("generated_at_kyiv") or row.get("generated_at") or "")))
            row.setdefault("title_ru", row.get("title"))
        return {"ok": True, "items": items}

    async def get_analysis(self, organization_id: str, analysis_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        listed = await self.list_analyses(organization_id, role)
        item = next((r for r in listed.get("items") or [] if str(r.get("id")) == str(analysis_id)), None)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Анализ не найден"}
        return {"ok": True, "item": item}

    async def analysis_create_notification(
        self, organization_id: str, analysis_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "intel")
        if denied:
            return denied
        got = await self.get_analysis(organization_id, analysis_id, role)
        if not got.get("ok"):
            return got
        item = got["item"]
        title = str(body.get("title") or f"Следить: {item.get('title_ru') or item.get('title')}")
        note = await self._emit_notification(  # type: ignore[attr-defined]
            organization_id,
            title=title,
            entity_type="analysis_run",
            entity_id=analysis_id,
            deeplink="/workspace/agro?view=analytics",
            extra={
                "kind": body.get("kind") or "analysis",
                "analysis_id": analysis_id,
                "commodity": body.get("commodity") or item.get("topic_ru"),
                "trigger": body.get("trigger") or "new_info",
            },
        )
        rule = None
        if body.get("target_price") not in (None, ""):
            rule = await self.create_entity(  # type: ignore[attr-defined]
                organization_id,
                "alert_rule",
                {
                    "target_price": body.get("target_price"),
                    "commodity": body.get("commodity") or item.get("topic_ru") or "Пшеница",
                    "operator": body.get("operator") or "gt",
                    "analysis_id": analysis_id,
                    "title": title,
                },
                role,
            )
        return {"ok": True, "item": note, "alert_rule": (rule or {}).get("item")}

    async def analysis_create_task(
        self, organization_id: str, analysis_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        got = await self.get_analysis(organization_id, analysis_id, role)
        if not got.get("ok"):
            return got
        item = got["item"]
        payload = {
            **body,
            "title": body.get("title") or f"Связаться с контрагентами по {(item.get('topic_ru') or 'рынку')}",
            "entity_type": "analysis_run",
            "entity_id": analysis_id,
            "analysis_id": analysis_id,
            "commodity": body.get("commodity") or item.get("topic_ru"),
        }
        return await self.create_task_from_entity(organization_id, payload, role)  # type: ignore[attr-defined]

    async def analysis_create_calendar(
        self, organization_id: str, analysis_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        got = await self.get_analysis(organization_id, analysis_id, role)
        if not got.get("ok"):
            return got
        item = got["item"]
        return await self.create_entity(  # type: ignore[attr-defined]
            organization_id,
            "calendar",
            {
                "title": body.get("title") or f"Follow-up: {item.get('title_ru') or item.get('title')}",
                "starts_at": body.get("starts_at") or _now(),
                "event_type": body.get("event_type") or "review_followup",
                "entity_type": "analysis_run",
                "entity_id": analysis_id,
                "analysis_id": analysis_id,
            },
            role,
        )

    async def run_pipeline(
        self,
        organization_id: str,
        role: str | None = None,
        *,
        fetch: str | None = "full",
        analysis_type: str | None = None,
        reports: list[str] | None = None,
        record_full_refresh: bool = False,
    ) -> dict[str, Any]:
        """FETCH → RAW STORE → NORMALIZE → VALIDATE → DEDUPE → freshness → usability → analysts → report."""
        import time

        from services.agro_ops.quality import PIPELINE_VERSION, validate_observations
        from services.agro_ops.service import _org

        denied = require(role, "intel")
        if denied:
            return denied
        steps: list[str] = []
        started = time.monotonic()
        ingested: dict[str, Any] = {"ok": True, "items": []}
        if fetch is not None:
            cadence = None if fetch in {"full", "all", ""} else fetch
            ingested = await self.ingest_providers(organization_id, role, cadence=cadence)  # type: ignore[attr-defined]
            steps.extend(["FETCH", "RAW_STORE", "NORMALIZE"])

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        observations = [
            o
            for o in self._observation_items(org)  # type: ignore[attr-defined]
            if o.get("record_kind") not in {"provider_raw", "provider_snapshot"}
            and str(o.get("data_class") or "") != "demo"
            and not o.get("is_demo")
        ]
        observations.extend(self._manual_price_observations(org))
        quality_flags = validate_observations(observations)
        steps.extend(["VALIDATE", "DEDUPLICATE"])
        status = await self.providers_status(org, role)  # type: ignore[attr-defined]
        freshness = self.provider_freshness_board(status.get("items") or [], observations)
        steps.extend(["CLASSIFY_FRESHNESS", "CLASSIFY_MARKET_USABILITY"])

        analysis: dict[str, Any] | None = None
        if analysis_type:
            analysis_res = await self.run_analysis(organization_id, {"analysis_type": analysis_type}, role)
            if not analysis_res.get("ok"):
                return analysis_res
            analysis = analysis_res.get("item")
            steps.extend(["SPECIALIST_ANALYSTS", "CHIEF_ANALYST"])

        reports_generated: list[str] = []
        report_items: list[dict[str, Any]] = []
        for kind in reports or []:
            gen = await self.generate_report(organization_id, kind, role, force=True)  # type: ignore[attr-defined]
            if gen.get("ok"):
                reports_generated.append(kind)
                if gen.get("item"):
                    report_items.append(gen["item"])
        if reports:
            steps.extend(["REPORT", "NOTIFICATIONS"])

        duration = round(time.monotonic() - started, 2)
        if record_full_refresh or fetch == "full":
            await self._save_refresh_meta(org, role, duration_sec=duration)  # type: ignore[attr-defined]
        return {
            **ingested,
            "ok": True,
            "pipeline_version": PIPELINE_VERSION,
            "pipeline_steps": steps,
            "quality_flags": quality_flags,
            "freshness": freshness,
            "analysis": analysis,
            "reports_generated": reports_generated,
            "reports": report_items,
            "refresh_duration_sec": duration,
        }

    async def rebuild_after_fix(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        """Обновить все → Пересчитать анализ → morning/evening/weekly/outlook with AGRO_1_9."""
        from services.agro_ops.quality import PIPELINE_VERSION

        denied = require(role, "intel")
        if denied:
            return denied
        refresh = await self.run_pipeline(
            organization_id, role, fetch="full", analysis_type=None, reports=[], record_full_refresh=True
        )
        if not refresh.get("ok"):
            return refresh
        analyses: dict[str, Any] = {}
        for analysis_type in ("operational", "morning", "evening", "weekly", "outlook"):
            res = await self.run_analysis(organization_id, {"analysis_type": analysis_type}, role)
            analyses[analysis_type] = {"ok": res.get("ok"), "id": (res.get("item") or {}).get("id"), "confidence": (res.get("item") or {}).get("confidence")}
            if res.get("ok") and analysis_type == "operational":
                refresh["pipeline_steps"] = list(refresh.get("pipeline_steps") or []) + ["SPECIALIST_ANALYSTS", "CHIEF_ANALYST"]
        report_kinds = ("morning", "evening", "weekly", "outlook")
        reports_generated: list[str] = []
        items: list[dict[str, Any]] = []
        for kind in report_kinds:
            gen = await self.generate_report(organization_id, kind, role, force=True)  # type: ignore[attr-defined]
            if gen.get("ok"):
                reports_generated.append(kind)
                if gen.get("item"):
                    items.append(gen["item"])
        refresh["pipeline_steps"] = list(refresh.get("pipeline_steps") or []) + ["REPORT", "NOTIFICATIONS"]
        return {
            "ok": True,
            "pipeline_version": PIPELINE_VERSION,
            "pipeline_steps": refresh.get("pipeline_steps"),
            "refresh": {k: refresh.get(k) for k in ("ok", "items", "refresh_duration_sec", "quality_flags") if k in refresh},
            "analyses": analyses,
            "reports_generated": reports_generated,
            "reports": items,
        }

