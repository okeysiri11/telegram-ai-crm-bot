"""AGRO 1.8 — gap severity, logistics/risk/opportunity engines, lineage helpers.

Never invent freight, prices, tonnes, or FX. Unknown sources do not drive
high-confidence conclusions.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

NO_RATE_RU = "Нет актуальной коммерческой ставки"


def lineage_from_obs(obs: dict[str, Any] | None) -> dict[str, Any] | None:
    if not obs:
        return None
    return {
        "provider_id": obs.get("provider_id") or obs.get("source"),
        "observation_id": obs.get("id"),
        "date": obs.get("observed_at") or obs.get("published_at") or obs.get("ingested_at"),
        "value": obs.get("normalized_value") if obs.get("normalized_value") is not None else obs.get("value"),
        "unit": obs.get("unit"),
        "url": obs.get("source_url"),
        "title": obs.get("title") or obs.get("text"),
    }


def _unknown(obs: dict[str, Any]) -> bool:
    if str(obs.get("data_class") or "") == "manual":
        return str(obs.get("manual_status") or "CONFIRMED").upper() != "CONFIRMED"
    if str(obs.get("source_class") or "") == "UNKNOWN":
        return True
    if str(obs.get("trust_level") or "").upper() == "LOW":
        return True
    return False


def production_observations(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from services.agro_ops.analytics import is_numeric_observation

    return [
        o
        for o in observations
        if is_numeric_observation(o)
        and not o.get("is_demo")
        and str(o.get("data_class") or "") != "demo"
        and not _unknown(o)
    ]


def structured_data_gaps(
    org: str,
    providers: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    *,
    trips: list[dict[str, Any]] | None = None,
    quotes: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    by_id = {str(p.get("id") or p.get("provider_id")): p for p in providers}
    numeric = production_observations(observations)
    kinds = {str(o.get("series_kind") or "") for o in numeric}
    rows: list[dict[str, Any]] = []

    def add(severity: str, text: str, code: str) -> None:
        rows.append({"severity": severity, "text": text, "code": code})

    if "weather" not in kinds:
        add("CRITICAL", "Нет числового ряда основной погоды.", "primary_weather")
    if "price" not in kinds:
        add("CRITICAL", "Нет официальных ценовых рядов.", "all_prices")

    priced = [
        t
        for t in list(trips or []) + freight_quotes_as_trips(quotes)
        if not t.get("is_demo")
        and (t.get("tariff") not in (None, "") or t.get("rate") not in (None, "") or t.get("cost") not in (None, "") or t.get("total_logistics_cost") not in (None, 0, "0"))
    ]
    if not priced:
        add("IMPORTANT", "Данных по логистическим тарифам недостаточно.", "logistics_rates")

    usda = by_id.get("usda_wasde") or {}
    if str(usda.get("health_state") or "") in {"PARTIAL", "METADATA_ONLY", "NEEDS_KEY", "FAILED"}:
        add("IMPORTANT", "USDA WASDE: нет числового баланса (нужен USDA_FAS_API_KEY или публичный JSON).", "usda_wasde")

    market = by_id.get("market_prices") or {}
    if str(market.get("health_state") or "") in {"NEEDS_KEY", "NEEDS_LICENSE", "REQUIRES_CONFIGURATION", "OPTIONAL_NOT_CONFIGURED", ""}:
        if "price" in kinds:
            add("OPTIONAL", "Лицензируемые биржевые котировки не подключены; есть официальные EU-цены.", "licensed_quotes")
        else:
            add("CRITICAL", "Рыночные биржевые котировки не подключены (лицензия / ключ).", "licensed_quotes")

    secondary = by_id.get("weather_provider_secondary") or {}
    if str(secondary.get("health_state") or "") in {"NEEDS_KEY", "OPTIONAL_NOT_CONFIGURED", "REQUIRES_CONFIGURATION", "NOT_CONFIGURED", ""}:
        add("OPTIONAL", "Резервный погодный провайдер не настроен.", "secondary_weather")

    minagro = by_id.get("ua_agro_ministry") or {}
    if str(minagro.get("health_state") or "") in {"BLOCKED", "FAILED"}:
        if "production" in kinds or "yield" in kinds or "area" in kinds:
            add("OPTIONAL", "Минагрополитики заблокирован (HTTP 403); есть альтернативные официальные ряды (World Bank / Eurostat).", "minagro_blocked")
        else:
            add("IMPORTANT", f"Минагрополитики: {minagro.get('note_ru') or 'BLOCKED'}", "minagro_blocked")

    has_qcl = any(str(o.get("series_id") or "").startswith("faostat-") and o.get("series_kind") == "production" for o in numeric)
    has_fpi = any(str(o.get("series_id") or "") == "faostat-fpi-cereals" for o in numeric)
    if not has_qcl:
        extra = " Есть FAO Food Price Index (Cereals), не тонны QCL." if has_fpi else ""
        add(
            "OPTIONAL" if has_fpi or "production" in kinds else "IMPORTANT",
            "FAOSTAT QCL (тонны производства) недоступен." + extra,
            "faostat_qcl",
        )

    customs = by_id.get("ua_customs_open_data") or {}
    if str(customs.get("health_state") or "") in {"PARTIAL", "METADATA_ONLY"} and "trade" in kinds:
        add("OPTIONAL", "Таможня data.gov.ua — только каталог; товарный экспорт/импорт есть у World Bank.", "customs_tonnes")

    for p in providers:
        health = str(p.get("health_state") or "")
        pid = str(p.get("id") or "")
        if health == "FAILED" and pid not in {"fao", "usda_wasde"}:
            add("IMPORTANT", f"{p.get('label_ru') or pid}: {p.get('note_ru') or health}", f"failed_{pid}")

    # de-dupe by code keeping highest severity
    rank = {"CRITICAL": 0, "IMPORTANT": 1, "OPTIONAL": 2}
    best: dict[str, dict[str, Any]] = {}
    for row in rows:
        prev = best.get(row["code"])
        if prev is None or rank[row["severity"]] < rank[prev["severity"]]:
            best[row["code"]] = row
    ordered = sorted(best.values(), key=lambda r: (rank[r["severity"]], r["code"]))
    return ordered


def freight_quotes_as_trips(market_prices: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in market_prices or []:
        if p.get("is_demo") or str(p.get("data_class") or "") == "demo":
            continue
        if str(p.get("price_kind") or "") != "freight":
            continue
        try:
            rate = float(p.get("price") or p.get("normalized_value") or 0)
        except (TypeError, ValueError):
            continue
        if rate <= 0:
            continue
        out.append(
            {
                "id": p.get("id"),
                "title": p.get("title") or p.get("name") or "MANUAL DATA · фрахт",
                "name": p.get("name") or "MANUAL DATA · фрахт",
                "rate": rate,
                "tariff": rate,
                "cost_per_tonne": rate,
                "currency": p.get("currency") or "USD",
                "is_demo": False,
                "manual_status": str(p.get("manual_status") or "CONFIRMED").upper(),
                "data_class": "manual",
            }
        )
    return out


def build_logistics_status(
    observations: list[dict[str, Any]],
    trips: list[dict[str, Any]],
    providers: list[dict[str, Any]],
    quotes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    numeric = production_observations(observations)
    freight = [o for o in numeric if "freight" in str(o.get("title") or "").lower() or o.get("series_kind") == "freight"]
    port_meta = [
        o
        for o in observations
        if str(o.get("provider_id")) == "ua_ports" or "port" in str(o.get("sections") or ())
    ]
    priced = []
    for t in list(trips or []) + freight_quotes_as_trips(quotes):
        if t.get("is_demo"):
            continue
        rate = t.get("rate") or t.get("tariff") or t.get("cost") or t.get("total_logistics_cost") or t.get("cost_per_tonne")
        if rate in (None, "", 0, "0"):
            continue
        priced.append(t)
    priced.sort(key=lambda t: float(t.get("cost_per_tonne") or t.get("rate") or t.get("tariff") or 10**12))
    cheapest = priced[0] if priced else None
    expensive = priced[-1] if priced else None
    rate_change = None
    if len(priced) >= 2:
        try:
            a = float(priced[0].get("cost_per_tonne") or priced[0].get("rate") or 0)
            b = float(priced[-1].get("cost_per_tonne") or priced[-1].get("rate") or 0)
            if a and b:
                rate_change = round((b - a) / a * 100, 1)
        except (TypeError, ValueError):
            rate_change = None
    ports_hs = next((p.get("health_state") for p in providers if p.get("id") == "ua_ports"), "")
    checks = ["Сверить внутренний rate book и фактические рейсы"]
    if not priced:
        checks.append("Добавить ручную коммерческую ставку — внешний фрахт не выдумывается")
    if port_meta:
        checks.append("Порталы портов дали только метаданные страниц, не ставки")
    return {
        "status_ru": "Есть внутренние ставки" if priced else NO_RATE_RU,
        "rate_change_pct": rate_change,
        "route_pressure_ru": "Недостаточно внешних данных о загрузке маршрутов" if not freight else "Есть внешний ряд фрахта",
        "cheapest_route": (
            {
                "text": f"{cheapest.get('title') or cheapest.get('name') or 'рейс'} {cheapest.get('cost_per_tonne') or cheapest.get('rate')} {cheapest.get('currency') or ''}".strip(),
                "sources": [lineage_from_obs({**cheapest, "provider_id": "ados_logistics", "source_url": None})],
            }
            if cheapest
            else {"text": NO_RATE_RU, "sources": []}
        ),
        "expensive_routes": (
            [
                {
                    "text": f"{expensive.get('title') or 'рейс'} {expensive.get('cost_per_tonne') or expensive.get('rate')} {expensive.get('currency') or ''}".strip(),
                    "sources": [lineage_from_obs({**expensive, "provider_id": "ados_logistics"})],
                }
            ]
            if expensive and expensive is not cheapest
            else []
        ),
        "risk_ru": "Порт: только страница/каталог" if str(ports_hs) in {"PARTIAL", "METADATA_ONLY"} else ("Нет коммерческой ставки" if not priced else "Ставки только внутренние ADOS"),
        "recommended_checks": checks,
        "commercial_rate": bool(priced),
        "findings": (
            [{"text": f"Внутренняя ставка: {cheapest.get('title')} {cheapest.get('rate') or cheapest.get('cost_per_tonne')}", "source": "ADOS", "record_id": cheapest.get("id")}]
            if cheapest
            else [{"text": NO_RATE_RU, "source": "ADOS"}]
        )
        + [{"text": o.get("title") or o.get("text"), "source": o.get("provider_id"), "record_id": o.get("id"), "metadata_only": True} for o in port_meta[:4]],
    }


def build_opportunities(
    observations: list[dict[str, Any]],
    trips: list[dict[str, Any]],
    fx_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Potential (not guaranteed) spread when dimensions match. No invented freight."""
    prices = [
        o
        for o in production_observations(observations)
        if o.get("series_kind") == "price" and o.get("normalized_value") is not None
    ]
    by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for o in prices:
        commodity = str(o.get("commodity") or "").strip() or "—"
        unit = str(o.get("unit") or "").strip()
        currency = str(o.get("currency") or "").strip()
        if not unit:
            continue
        by_key[(commodity, unit, currency)].append(o)
    logistics_cost = None
    logistics_note = NO_RATE_RU
    logistics_src: list[dict[str, Any]] = []
    for t in trips:
        if t.get("is_demo"):
            continue
        val = t.get("cost_per_tonne") or t.get("rate") or t.get("tariff")
        try:
            number = float(val)
        except (TypeError, ValueError):
            continue
        if number > 0:
            logistics_cost = number
            logistics_note = f"Внутренняя ставка ADOS {number} {t.get('currency') or ''}".strip()
            logistics_src = [lineage_from_obs({**t, "provider_id": "ados_logistics", "normalized_value": number}) or {}]
            break
    fx = production_observations(fx_rows or [o for o in observations if o.get("series_kind") == "fx"])
    out: list[dict[str, Any]] = []
    for (commodity, unit, currency), rows in by_key.items():
        latest: dict[str, dict[str, Any]] = {}
        for row in rows:
            market = str(row.get("country") or row.get("provider_id") or "")
            prev = latest.get(market)
            if prev is None or str(row.get("observed_at") or "") >= str(prev.get("observed_at") or ""):
                latest[market] = row
        markets = list(latest.values())
        if len(markets) < 2:
            continue
        markets.sort(key=lambda r: float(r.get("normalized_value") or 0))
        buy, sell = markets[0], markets[-1]
        try:
            buy_v = float(buy["normalized_value"])
            sell_v = float(sell["normalized_value"])
        except (TypeError, ValueError, KeyError):
            continue
        if sell_v <= buy_v:
            continue
        diff = round(sell_v - buy_v, 4)
        gross = diff
        if logistics_cost is not None:
            gross = round(diff - logistics_cost, 4)
        sources = [x for x in (lineage_from_obs(buy), lineage_from_obs(sell), *(logistics_src or []), *(lineage_from_obs(x) for x in fx[:1])) if x]
        confidence = "medium" if logistics_cost is not None else "low"
        out.append(
            {
                "kind": "potential_opportunity",
                "guaranteed_profit": False,
                "label_ru": "Потенциальная возможность",
                "text": (
                    f"Потенциальная возможность: {commodity} {buy.get('country')} → {sell.get('country')} "
                    f"спред {diff} {currency}/{unit}. Не гарантированная прибыль."
                ),
                "commodity": commodity,
                "buy_market": buy.get("country") or buy.get("provider_id"),
                "sell_market": sell.get("country") or sell.get("provider_id"),
                "price_difference": diff,
                "estimated_logistics": logistics_cost,
                "estimated_logistics_note": logistics_note,
                "fx": [{"title": x.get("title"), "value": x.get("normalized_value"), "commodity": x.get("commodity")} for x in fx[:2]],
                "gross_spread": gross,
                "data_confidence": confidence,
                "currency": currency,
                "unit": unit,
                "sources": sources,
            }
        )
    if not out:
        out.append(
            {
                "kind": "potential_opportunity",
                "guaranteed_profit": False,
                "label_ru": "Потенциальная возможность",
                "text": (
                    "Потенциальная возможность не рассчитана: нет двух совместимых ценовых рядов "
                    "(товар, единица, валюта) плюс ставка логистики. Не гарантированная прибыль."
                ),
                "commodity": None,
                "buy_market": None,
                "sell_market": None,
                "price_difference": None,
                "estimated_logistics": None,
                "estimated_logistics_note": logistics_note,
                "fx": [{"title": x.get("title"), "value": x.get("normalized_value"), "commodity": x.get("commodity")} for x in fx[:2]],
                "gross_spread": None,
                "data_confidence": "low",
                "sources": [s for s in (lineage_from_obs(x) for x in fx[:1]) if s],
            }
        )
    return out[:8]


def _vol_pct(points: list[dict[str, Any]]) -> float | None:
    vals = []
    for p in sorted(points, key=lambda r: str(r.get("observed_at") or "")):
        try:
            vals.append(float(p.get("normalized_value")))
        except (TypeError, ValueError):
            continue
    if len(vals) < 2 or not vals[0]:
        return None
    return round((vals[-1] - vals[0]) / abs(vals[0]) * 100, 2)


def build_risks(
    observations: list[dict[str, Any]],
    providers: list[dict[str, Any]],
    internal: dict[str, list[dict[str, Any]]] | None = None,
    *,
    lots: list[dict[str, Any]] | None = None,
    contracts: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    internal = internal or {}
    numeric = production_observations(observations)
    risks: list[dict[str, Any]] = []

    def add(level: str, text: str, reason: str, sources: list[Any]) -> None:
        risks.append(
            {
                "level": level,
                "text": text,
                "reason": reason,
                "sources": [s for s in sources if s],
            }
        )

    weather = [o for o in numeric if o.get("series_kind") == "weather"]
    if any(str(o.get("weather_risk") or "").upper() == "HIGH" for o in weather):
        hit = next(o for o in weather if str(o.get("weather_risk") or "").upper() == "HIGH")
        add("HIGH", str(hit.get("text") or hit.get("title") or "Погодный риск HIGH"), "weather HIGH from Open-Meteo (or labelled weather series)", [lineage_from_obs(hit)])
    if not weather:
        add("CRITICAL", "Нет числового ряда основной погоды.", "primary weather missing", [])

    prices = [o for o in numeric if o.get("series_kind") == "price"]
    vol = _vol_pct(prices)
    if vol is not None and abs(vol) >= 8:
        level = "HIGH" if abs(vol) >= 15 else "MEDIUM"
        add(level, f"Волатильность официальных цен {vol}% на доступном окне.", "price series change", [lineage_from_obs(prices[0]), lineage_from_obs(prices[-1])])

    fx = [o for o in numeric if o.get("series_kind") == "fx"]
    by_cc: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for o in fx:
        by_cc[str(o.get("commodity") or o.get("series_id") or "fx")].append(o)
    for code, rows in by_cc.items():
        change = _vol_pct(rows)
        if change is not None and abs(change) >= 1.5:
            add("MEDIUM", f"Движение курса {code} {change}%.", "FX series", [lineage_from_obs(rows[0]), lineage_from_obs(rows[-1])])

    ports = next((p for p in providers if p.get("id") == "ua_ports"), None)
    if ports and str(ports.get("health_state")) in {"PARTIAL", "METADATA_ONLY"}:
        add("LOW", "Порты: только страница/каталог, нет числовой загрузки.", "port metadata only", [])
    if ports and str(ports.get("health_state")) in {"FAILED", "BLOCKED"}:
        add("HIGH", "Источник портов недоступен.", "port feed failed", [])

    for item in internal.get("risks") or []:
        add("HIGH", str(item.get("text") or item), "internal ADOS (overdue / contracts)", [])

    today = datetime.now(timezone.utc).date().isoformat()
    for c in contracts or []:
        if c.get("is_demo"):
            continue
        end = str(c.get("end_at") or "")[:10]
        if end and end <= today:
            add("HIGH", f"Договор истекает или истёк: {c.get('title')} ({end})", "contract deadline", [])

    low_lots = [lt for lt in (lots or []) if not lt.get("is_demo")]
    try:
        qty = sum(float(lt.get("quantity") or lt.get("qty") or 0) for lt in low_lots)
    except (TypeError, ValueError):
        qty = 0.0
    if low_lots and qty <= 0:
        add("MEDIUM", "Низкие или нулевые остатки на складе.", "inventory", [])

    failed = [p for p in providers if str(p.get("health_state")) == "FAILED"]
    if failed:
        add("MEDIUM", f"Деградация источников: {', '.join(str(p.get('label_ru')) for p in failed[:3])}.", "data deterioration", [])

    rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    risks.sort(key=lambda r: rank.get(str(r.get("level")), 9))
    return risks[:12]
