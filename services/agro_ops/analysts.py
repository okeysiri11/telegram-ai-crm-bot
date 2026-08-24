"""AGRO 1.4 — specialist analyst pipeline.

Analysts consume normalized observations only (never raw HTML).
Each specialist output is persisted with input traceability.
Chief confidence is calculated, never hardcoded.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from services.agro_ops.rbac import require

SPECIALISTS = [
    ("ukraine", "Агент по Украине", ("ukraine", "harvest", "trade")),
    ("market", "Рыночный агент", ("prices", "world")),
    ("price", "Ценовой агент", ("prices",)),
    ("weather", "Погодный агент", ("weather",)),
    ("crop", "Агент по урожаю", ("harvest",)),
    ("trade", "Торговый агент", ("trade",)),
    ("logistics", "Логистический агент", ("logistics",)),
    ("ports", "Портовый агент", ("logistics", "trade")),
    ("risk", "Риск-агент", ("risks",)),
    ("opportunity", "Агент возможностей", ("opportunities", "prices")),
    ("global", "Агент мировых рынков", ("world", "prices")),
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _freshness_score(items: list[dict[str, Any]]) -> float:
    if not items:
        return 0.0
    now = datetime.now(timezone.utc)
    scores = []
    for item in items:
        raw = str(item.get("ingested_at") or item.get("published_at") or "")
        try:
            ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            hours = max(0.0, (now - ts).total_seconds() / 3600)
        except Exception:
            hours = 72.0
        if hours <= 24:
            scores.append(1.0)
        elif hours <= 72:
            scores.append(0.6)
        else:
            scores.append(0.25)
    return sum(scores) / len(scores)


def calculate_chief_confidence(
    *,
    coverage: float,
    freshness: float,
    quality: float,
    agreement: float,
    missing_ratio: float,
) -> int:
    value = (
        0.30 * coverage
        + 0.25 * freshness
        + 0.20 * quality
        + 0.15 * agreement
        + 0.10 * max(0.0, 1.0 - missing_ratio)
    )
    return int(max(0, min(100, round(value * 100))))


class AgroOpsAnalystMixin:
    """Mixed into AgroOpsService — stored specialist outputs."""

    async def run_agents(self, organization_id: str, body: dict[str, Any] | None = None, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "ai")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        intel = self._intel_items(org)  # type: ignore[attr-defined]
        internal = self._internal_bullets(org)  # type: ignore[attr-defined]
        observations = [o for o in self._observation_items(org) if o.get("record_kind") != "provider_raw"]  # type: ignore[attr-defined]
        body = body or {}
        filtered = body.get("_filtered_observations")
        if isinstance(filtered, list):
            observations = filtered
        elif any(body.get(k) for k in ("crop", "country", "region", "period", "source", "question", "query")):
            observations = self._filter_observations(observations, body)  # type: ignore[attr-defined]
        observations = [o for o in observations if str(o.get("data_class") or "") != "demo" and not o.get("is_demo")]
        status = await self.providers_status(org, role)  # type: ignore[attr-defined]
        providers = status.get("items") or []
        connected = [
            p
            for p in providers
            if str(p.get("health_state") or p.get("connection_status"))
            in {"CONNECTED", "PARTIAL", "DEGRADED", "METADATA_ONLY"}
        ]
        failed = [p for p in providers if str(p.get("health_state") or p.get("probe_result")) in {"FAILED", "BLOCKED"}]
        bag = self._bag(org)  # type: ignore[attr-defined]
        trips = active_only(bag.get("trip") or [])
        lots = active_only(bag.get("inventory_lot") or [])
        contracts = active_only(bag.get("contract") or [])
        quotes = active_only(bag.get("market_price") or [])
        from services.agro_ops.engines import (
            build_logistics_status,
            build_opportunities,
            build_risks,
            lineage_from_obs,
            production_observations,
            structured_data_gaps,
        )

        prod_obs = production_observations(observations)
        logistics_status = build_logistics_status(observations, trips, providers, quotes=quotes)
        opportunities = build_opportunities(observations, trips)
        engine_risks = build_risks(observations, providers, internal, lots=lots, contracts=contracts)
        gaps_structured = structured_data_gaps(org, providers, observations, trips=trips, quotes=quotes)

        run_id = str(uuid.uuid4())
        started_run = _now()
        specialist_rows: list[dict[str, Any]] = []

        for agent_id, label, sections in SPECIALISTS:
            started = _now()
            obs_items = [o for o in observations if any(s in (o.get("sections") or ()) for s in sections)]
            if agent_id == "ports":
                obs_items = [
                    o
                    for o in observations
                    if str(o.get("provider_id")) == "ua_ports" or "port" in str(o.get("title") or "").lower()
                ]
            intel_items = [i for i in intel if i.get("section") in sections]
            findings: list[dict[str, Any]] = [
                {
                    "text": i.get("title"),
                    "source": i.get("source"),
                    "source_url": i.get("source_url"),
                    "confidence": i.get("confidence"),
                    "record_id": i.get("id"),
                    "sources": [lineage_from_obs(i)],
                }
                for i in intel_items[:8]
            ]
            findings.extend(
                {
                    "text": o.get("text") or o.get("title"),
                    "source": o.get("provider_id"),
                    "source_url": o.get("source_url"),
                    "confidence": o.get("confidence"),
                    "record_id": o.get("id"),
                    "kind": "observation",
                    "canonical_type": o.get("canonical_type"),
                    "data_class": o.get("data_class"),
                    "value": o.get("normalized_value"),
                    "unit": o.get("unit"),
                    "sources": [lineage_from_obs(o)],
                }
                for o in obs_items[:12]
                if str(o.get("data_class") or "") != "demo"
            )
            if agent_id == "logistics":
                findings = list(logistics_status.get("findings") or [])
                for row in findings:
                    row.setdefault("sources", [])
            elif agent_id == "opportunity":
                findings = [
                    {
                        "text": o.get("text"),
                        "source": "opportunity_engine",
                        "commodity": o.get("commodity"),
                        "buy_market": o.get("buy_market"),
                        "sell_market": o.get("sell_market"),
                        "price_difference": o.get("price_difference"),
                        "estimated_logistics": o.get("estimated_logistics"),
                        "estimated_logistics_note": o.get("estimated_logistics_note"),
                        "fx": o.get("fx"),
                        "gross_spread": o.get("gross_spread"),
                        "data_confidence": o.get("data_confidence"),
                        "sources": o.get("sources") or [],
                    }
                    for o in opportunities
                ]
            elif agent_id == "risk":
                findings = [
                    {
                        "text": r.get("text"),
                        "level": r.get("level"),
                        "reason": r.get("reason"),
                        "source": "risk_engine",
                        "sources": r.get("sources") or [],
                    }
                    for r in engine_risks
                ]
                findings.extend(internal.get("risks", []))
            input_ids = [str(x.get("id")) for x in obs_items[:20] + intel_items[:10] if x.get("id")]
            input_providers = sorted(
                {
                    str(x.get("provider_id") or x.get("source") or "")
                    for x in obs_items + intel_items
                    if x.get("provider_id") or x.get("source")
                }
            )
            gaps = []
            if not findings:
                gaps.append("DATA GAP: нет нормализованных наблюдений по этому направлению.")
            conclusion = findings[0]["text"] if findings else "Недостаточно нормализованных данных — вывод не формируется."
            item = {
                "id": str(uuid.uuid4()),
                "organization_id": org,
                "tenant_id": org,
                "record_type": "analyst_output",
                "run_id": run_id,
                "agent": agent_id,
                "title": label,
                "name": label,
                "input_provider_ids": input_providers,
                "input_record_ids": input_ids,
                "started_at": started,
                "finished_at": _now(),
                "data_freshness": "LIVE" if obs_items or findings else "NOT_CONFIGURED",
                "conclusion": conclusion,
                "confidence": "medium" if findings else "low",
                "data_gaps": gaps,
                "findings": findings,
                "status": "active",
                "created_at": _now(),
            }
            saved = await self._persist("analyst_output", item)  # type: ignore[attr-defined]
            self._bag(org)["analyst_output"].insert(0, saved)  # type: ignore[attr-defined]
            specialist_rows.append(saved)

        expected_cats = {"trade", "weather", "prices", "world", "harvest", "ukraine", "logistics"}
        covered = {
            s
            for row in specialist_rows
            for s in (next((sp[2] for sp in SPECIALISTS if sp[0] == row.get("agent")), ()))
            if row.get("findings")
        }
        coverage = len(covered & expected_cats) / len(expected_cats)
        freshness = _freshness_score(prod_obs or observations)
        connected_n = len([p for p in connected if p.get("health_state") == "CONNECTED" and p.get("id") != "manual_import"])
        partial_n = len([p for p in connected if p.get("health_state") in {"PARTIAL", "METADATA_ONLY"}])
        quality = min(1.0, (connected_n + 0.35 * partial_n) / 4)
        from services.agro_ops.analytics import is_metadata_observation

        page_ratio = 0.0
        if observations:
            page_ratio = sum(1 for o in observations if is_metadata_observation(o)) / len(observations)
        if page_ratio >= 0.5:
            quality *= 0.45
        with_findings = sum(1 for r in specialist_rows if r.get("findings"))
        agreement = with_findings / max(1, len(SPECIALISTS))
        missing_ratio = 1.0 - agreement
        confidence = calculate_chief_confidence(
            coverage=coverage,
            freshness=freshness * (0.7 if page_ratio >= 0.5 else 1.0),
            quality=quality,
            agreement=agreement,
            missing_ratio=missing_ratio,
        )
        if any(str(r.get("level")) in {"HIGH", "CRITICAL"} for r in engine_risks) or internal.get("risks"):
            bias = "RISK"
        elif with_findings >= 4 and quality >= 0.5:
            bias = "WATCH"
        elif with_findings:
            bias = "NEUTRAL"
        else:
            bias = "WATCH"
        freshness_board = self.provider_freshness_board(providers, observations)  # type: ignore[attr-defined]
        chief = {
            "agent": "chief",
            "label_ru": "Главный агро-аналитик",
            "bias": bias,
            "confidence": confidence,
            "key_drivers": [str(r.get("conclusion") or "") for r in specialist_rows if r.get("findings")][:5],
            "risks": engine_risks,
            "opportunities": opportunities,
            "logistics": logistics_status,
            "observations": [lineage_from_obs(o) for o in prod_obs[:40]],
            "specialist_conclusions": [
                {"agent": r.get("agent"), "label_ru": r.get("title"), "conclusion": r.get("conclusion")}
                for r in specialist_rows
            ],
            "freshness": freshness_board,
            "source_quality": {
                "connected": connected_n,
                "partial": partial_n,
                "failed": len(failed),
                "numeric_observations": len(prod_obs),
                "unknown_excluded": True,
            },
            "data_gaps_structured": gaps_structured,
            "what_to_watch": [
                "Официальные каталоги и страницы — не выдуманные котировки",
                "Просроченные оплаты и истекающие договоры (внутренние данные ADOS)",
            ],
            "note_ru": (
                f"Главный вывод основан на {len(prod_obs)} числовых наблюдениях "
                f"(из {len(observations)} нормализованных) и {len(connected)} доступных источниках. "
                "Сырой HTML не анализировался. Цены и тонны не выдумываются. "
                "UNKNOWN/LOW не входят в high-confidence анализ. DEMO исключён."
                + (
                    " Поступили в основном метаданные каталогов/страниц, а не рыночные ряды."
                    if page_ratio >= 0.5
                    else " Числовые ряды официальных API использованы без экстраполяции."
                )
            ),
            "input_provider_ids": sorted({str(p.get("id")) for p in connected if p.get("id")}),
            "started_at": started_run,
            "finished_at": _now(),
            "data_gaps": [g["text"] for g in gaps_structured][:12],
        }
        chief_row = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "record_type": "analyst_output",
            "run_id": run_id,
            "agent": "chief",
            "title": "Главный агро-аналитик",
            "name": "Главный агро-аналитик",
            "input_provider_ids": chief["input_provider_ids"],
            "input_record_ids": [str(r.get("id")) for r in specialist_rows],
            "started_at": started_run,
            "finished_at": _now(),
            "data_freshness": "LIVE" if observations else "NOT_CONFIGURED",
            "conclusion": bias,
            "confidence": confidence,
            "data_gaps": chief["data_gaps"],
            "findings": [{"text": d} for d in chief["key_drivers"]],
            "status": "active",
            "created_at": _now(),
        }
        saved_chief = await self._persist("analyst_output", chief_row)  # type: ignore[attr-defined]
        self._bag(org)["analyst_output"].insert(0, saved_chief)  # type: ignore[attr-defined]

        envelope = {
            "id": run_id,
            "organization_id": org,
            "tenant_id": org,
            "record_type": "agents_run",
            "title": "Запуск агро-аналитиков",
            "name": "Запуск агро-аналитиков",
            "agents": [
                {
                    "agent": r.get("agent"),
                    "label_ru": r.get("title"),
                    "findings": r.get("findings") or [],
                    "data_gaps": r.get("data_gaps") or [],
                    "conclusion": r.get("conclusion"),
                    "input_provider_ids": r.get("input_provider_ids") or [],
                    "input_record_ids": r.get("input_record_ids") or [],
                    "started_at": r.get("started_at"),
                    "finished_at": r.get("finished_at"),
                    "confidence": r.get("confidence"),
                }
                for r in specialist_rows
            ],
            "chief": chief,
            "observation_count": len(observations),
            "specialists_executed": [r.get("agent") for r in specialist_rows] + ["chief"],
            "status": "active",
            "created_at": _now(),
        }
        saved = await self._persist("report", envelope)  # type: ignore[attr-defined]
        self._bag(org)["report"].insert(0, saved)  # type: ignore[attr-defined]
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org, entity_type="agents", entity_id=saved["id"], action="created",
            summary="Запуск агро-аналитиков", role=role,
        )
        return {"ok": True, "item": saved}

    async def list_agent_runs(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        items = [r for r in active_only(self._bag(org)["report"]) if r.get("record_type") == "agents_run"]  # type: ignore[attr-defined]
        return {"ok": True, "items": items}

    async def list_analyst_outputs(self, organization_id: str, role: str | None = None, run_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        items = active_only(self._bag(org).get("analyst_output") or [])  # type: ignore[attr-defined]
        if run_id:
            items = [i for i in items if str(i.get("run_id")) == str(run_id)]
        return {"ok": True, "items": items}
