"""AGRO 1.9 — source health, operational counts, validation, anomalies, charts.

Flags suspicious data. Never silently deletes. Manual CONFIRMED is first-class.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Any

PIPELINE_VERSION = "AGRO_1_9"
ANOMALY_PCT_DEFAULT = 8.0

HEALTHY_STATES = frozenset({"CONNECTED"})
PARTIAL_STATES = frozenset({"PARTIAL", "STALE", "METADATA_ONLY", "DEGRADED"})
NEEDS_KEY_STATES = frozenset({"NEEDS_KEY", "NEEDS_LICENSE"})
OPTIONAL_STATES = frozenset({"OPTIONAL_NOT_CONFIGURED"})
FAILED_STATES = frozenset({"BLOCKED", "FAILED"})


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(raw: Any) -> datetime | None:
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


def _num(obs: dict[str, Any]) -> float | None:
    try:
        v = obs.get("normalized_value")
        if v in (None, "", "null"):
            v = obs.get("value")
        if v in (None, ""):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def is_real_numeric(obs: dict[str, Any]) -> bool:
    from services.agro_ops.analytics import is_metadata_observation, is_numeric_observation

    if obs.get("is_demo") or str(obs.get("data_class") or "") == "demo":
        return False
    if is_metadata_observation(obs):
        return False
    return is_numeric_observation(obs)


def provider_health_summary(
    providers: list[dict[str, Any]],
    *,
    last_full_refresh_at: str | None = None,
    last_full_refresh_duration_sec: float | None = None,
) -> dict[str, Any]:
    healthy = partial = needs_key = optional = failed = 0
    for p in providers:
        if str(p.get("id") or "") == "manual_import":
            continue
        hs = str(p.get("health_state") or p.get("connection_status") or "")
        if hs in HEALTHY_STATES:
            healthy += 1
        elif hs in PARTIAL_STATES:
            partial += 1
        elif hs in NEEDS_KEY_STATES:
            needs_key += 1
        elif hs in OPTIONAL_STATES:
            optional += 1
        elif hs in FAILED_STATES:
            failed += 1
        elif hs in {"REQUIRES_CONFIGURATION", "NOT_CONFIGURED"}:
            optional += 1
    return {
        "title_ru": "ЗДОРОВЬЕ ИСТОЧНИКОВ",
        "healthy": healthy,
        "partial": partial,
        "needs_key": needs_key,
        "optional": optional,
        "failed": failed,
        "last_full_refresh_at": last_full_refresh_at,
        "refresh_duration_sec": last_full_refresh_duration_sec,
    }


def operational_counts(
    observations: list[dict[str, Any]],
    *,
    trips: list[dict[str, Any]] | None = None,
    market_prices: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    numeric = [o for o in observations if is_real_numeric(o)]
    now = _now()
    cutoff_24 = now - timedelta(hours=24)
    cutoff_7 = now - timedelta(days=7)
    fresh_24 = 0
    last_7 = 0
    historical = 0
    price = weather = trade = logistics = 0
    for o in numeric:
        ts = _parse_ts(o.get("observed_at") or o.get("ingested_at") or o.get("published_at"))
        if ts and ts >= cutoff_24:
            fresh_24 += 1
        if ts and ts >= cutoff_7:
            last_7 += 1
        else:
            historical += 1
        kind = str(o.get("series_kind") or "")
        if kind == "price":
            price += 1
        elif kind == "weather":
            weather += 1
        elif kind == "trade":
            trade += 1
        elif kind in {"freight", "logistics"}:
            logistics += 1
    for t in trips or []:
        if t.get("is_demo"):
            continue
        if t.get("rate") not in (None, "", 0, "0") or t.get("tariff") not in (None, "", 0, "0"):
            logistics += 1
    for p in market_prices or []:
        if p.get("is_demo"):
            continue
        if str(p.get("price_kind") or "") == "freight" and p.get("price") not in (None, "", 0, "0"):
            logistics += 1
    return {
        "numeric_observations": len(numeric),
        "fresh_24h": fresh_24,
        "last_7d": last_7,
        "historical": historical,
        "price": price,
        "weather": weather,
        "trade": trade,
        "logistics": logistics,
        "metadata_excluded": True,
    }


def _series_key(obs: dict[str, Any]) -> str:
    return str(obs.get("series_id") or f"{obs.get('provider_id')}:{obs.get('series_kind')}:{obs.get('commodity')}:{obs.get('unit')}")


def validate_observations(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flag issues. Never delete."""
    flags: list[dict[str, Any]] = []
    now = _now()
    seen: dict[tuple[Any, ...], dict[str, Any]] = {}
    by_series: dict[str, list[float]] = defaultdict(list)

    def add(code: str, text: str, obs: dict[str, Any] | None = None, severity: str = "IMPORTANT") -> None:
        flags.append(
            {
                "code": code,
                "text": text,
                "severity": severity,
                "observation_id": (obs or {}).get("id"),
                "provider_id": (obs or {}).get("provider_id"),
                "kept": True,
            }
        )

    for obs in observations:
        if obs.get("is_demo") or str(obs.get("data_class") or "") == "demo":
            continue
        if str(obs.get("record_kind") or "") in {"provider_raw", "provider_snapshot"}:
            continue
        value = _num(obs)
        ts = _parse_ts(obs.get("observed_at") or obs.get("published_at") or obs.get("ingested_at"))
        raw_date = str(obs.get("observed_at") or obs.get("published_at") or "")
        if raw_date and ts is None:
            add("date_sanity", "Дата не разбирается.", obs)
        if ts and ts > now + timedelta(days=1):
            add("future_date", "Дата наблюдения в будущем.", obs, "CRITICAL")
        if ts and ts.year < 1990:
            add("date_sanity", "Дата раньше 1990 — подозрительна.", obs)
        if is_real_numeric(obs):
            kind = str(obs.get("series_kind") or "")
            if kind in {"price", "trade", "production", "area", "yield", "freight"} and value is not None and value < 0:
                add("negative_impossible", "Отрицательное значение невозможно для этого ряда.", obs, "CRITICAL")
            if kind == "price" and (not obs.get("unit") or not (obs.get("currency") or obs.get("commodity"))):
                add("missing_dimensions", "У цены нет единицы/валюты/товара.", obs)
            if kind in {"weather", "fx"} and ts and now - ts > timedelta(hours=72):
                add("stale", "Свежий операционный ряд устарел (>72ч).", obs)
            fp = (
                obs.get("provider_id"),
                obs.get("series_id"),
                str(obs.get("observed_at") or "")[:16],
                value,
            )
            prev = seen.get(fp)
            if prev is not None:
                add("duplicate", "Повтор того же наблюдения (запись сохранена, не удалена).", obs)
            else:
                seen[fp] = obs
            if value is not None:
                by_series[_series_key(obs)].append(value)
        if str(obs.get("data_class")) == "manual" and str(obs.get("manual_status") or "CONFIRMED").upper() == "UNCONFIRMED":
            add("unconfirmed_manual", "Ручные данные UNCONFIRMED — не удалены, помечены.", obs, "OPTIONAL")

    for key, vals in by_series.items():
        if len(vals) < 4:
            continue
        mid = median(vals)
        if not mid:
            continue
        units = {str(o.get("unit") or "") for o in observations if _series_key(o) == key and is_real_numeric(o)}
        if len({u for u in units if u}) > 1:
            add("unit_consistency", f"В ряду {key} смешаны единицы: {', '.join(sorted(u for u in units if u))}.", None)
        for obs in observations:
            if _series_key(obs) != key or not is_real_numeric(obs):
                continue
            v = _num(obs)
            if v is None:
                continue
            if abs(v) > abs(mid) * 8:
                add("outlier", f"Выброс {v} против медианы {mid} ряда {key}.", obs)

    return flags[:80]


def detect_anomalies(observations: list[dict[str, Any]], *, threshold_pct: float = ANOMALY_PCT_DEFAULT) -> list[dict[str, Any]]:
    """ANOMALY only when enough comparable observations exist."""
    by_series: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for obs in observations:
        if not is_real_numeric(obs):
            continue
        by_series[_series_key(obs)].append(obs)
    out: list[dict[str, Any]] = []
    for key, rows in by_series.items():
        rows = sorted(rows, key=lambda r: str(r.get("observed_at") or r.get("published_at") or ""))
        if len(rows) < 3:
            continue
        units = {str(r.get("unit") or "") for r in rows}
        if len({u for u in units if u}) > 1:
            continue
        try:
            first = float(rows[0].get("normalized_value"))
            last = float(rows[-1].get("normalized_value"))
        except (TypeError, ValueError):
            continue
        if not first:
            continue
        change = (last - first) / abs(first) * 100
        kind = str(rows[0].get("series_kind") or "")
        extreme_weather = kind == "weather" and any(str(r.get("weather_risk") or "").upper() == "HIGH" for r in rows)
        production_revision = kind in {"production", "yield", "area"} and abs(change) >= threshold_pct
        price_or_fx = kind in {"price", "fx"} and abs(change) >= threshold_pct
        if not (extreme_weather or production_revision or price_or_fx):
            continue
        out.append(
            {
                "kind": "ANOMALY",
                "series_id": key,
                "series_kind": kind,
                "change_pct": round(change, 2),
                "text": (
                    f"ANOMALY: {kind} {key} изменение {round(change, 1)}% "
                    f"на {len(rows)} сопоставимых точках."
                ),
                "observation_ids": [r.get("id") for r in (rows[0], rows[-1])],
                "comparable_n": len(rows),
            }
        )
    return out[:20]


def sanitize_chart_series(buckets: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    """One metric per chart: ordered unique dates, no mixed units, no duplicate dates."""
    cleaned: dict[str, list[dict[str, Any]]] = {}
    for kind, rows in buckets.items():
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            groups[str(row.get("series_id") or row.get("source") or kind)].append(row)
        if not groups:
            cleaned[kind] = []
            continue
        best_id, best_rows = max(groups.items(), key=lambda kv: (len(kv[1]), str(kv[0])))
        units = [str(r.get("unit") or "") for r in best_rows]
        majority_unit = max(set(units), key=units.count) if units else ""
        by_date: dict[str, dict[str, Any]] = {}
        for row in best_rows:
            if majority_unit and str(row.get("unit") or "") not in {"", majority_unit}:
                continue
            day = str(row.get("t") or "")[:16]
            if not day:
                continue
            prev = by_date.get(day)
            if prev is None or str(row.get("t") or "") >= str(prev.get("t") or ""):
                by_date[day] = {**row, "metric": best_id, "unit": majority_unit or row.get("unit")}
        ordered = sorted(by_date.values(), key=lambda r: str(r.get("t") or ""))
        cleaned[kind] = ordered
    return cleaned
