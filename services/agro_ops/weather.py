"""AGRO 2.0 — Ukraine weather desk: regions, narratives, crop impact, history.

Never invent climate normals or fake oblast values. Missing data is explicit.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from services.agro_ops.rbac import require
from services.agro_ops.series_parsers import parse_open_meteo, to_float

MISSING_CLIMATE_RU = "Недостаточно данных для сравнения с климатической нормой."
MISSING_STATUS_RU = "Нет актуальных погодных данных по этому региону."

MACRO_REGIONS = [
    {"id": "south", "label_ru": "ЮГ УКРАИНЫ", "short_ru": "Юг"},
    {"id": "center", "label_ru": "ЦЕНТР УКРАИНЫ", "short_ru": "Центр"},
    {"id": "west", "label_ru": "ЗАПАД УКРАИНЫ", "short_ru": "Запад"},
    {"id": "north", "label_ru": "СЕВЕР УКРАИНЫ", "short_ru": "Север"},
    {"id": "east", "label_ru": "ВОСТОК УКРАИНЫ", "short_ru": "Восток"},
]

# Representative oblast seats. Coordinates are public geographic facts, not weather.
UA_OBLASTS: list[dict[str, Any]] = [
    {"id": "odesa", "label_ru": "Одесская область", "macro": "south", "lat": 46.48, "lon": 30.73},
    {"id": "mykolaiv", "label_ru": "Николаевская область", "macro": "south", "lat": 46.97, "lon": 32.00},
    {"id": "kherson", "label_ru": "Херсонская область", "macro": "south", "lat": 46.64, "lon": 32.62},
    {"id": "kyiv", "label_ru": "Киевская область", "macro": "center", "lat": 50.45, "lon": 30.52},
    {"id": "cherkasy", "label_ru": "Черкасская область", "macro": "center", "lat": 49.44, "lon": 32.06},
    {"id": "kropyvnytskyi", "label_ru": "Кировоградская область", "macro": "center", "lat": 48.51, "lon": 32.27},
    {"id": "vinnytsia", "label_ru": "Винницкая область", "macro": "center", "lat": 49.23, "lon": 28.47},
    {"id": "poltava", "label_ru": "Полтавская область", "macro": "center", "lat": 49.59, "lon": 34.55},
    {"id": "lviv", "label_ru": "Львовская область", "macro": "west", "lat": 49.84, "lon": 24.03},
    {"id": "ivano_frankivsk", "label_ru": "Ивано-Франковская область", "macro": "west", "lat": 48.92, "lon": 24.71},
    {"id": "ternopil", "label_ru": "Тернопольская область", "macro": "west", "lat": 49.55, "lon": 25.59},
    {"id": "zakarpattia", "label_ru": "Закарпатская область", "macro": "west", "lat": 48.62, "lon": 22.30},
    {"id": "volyn", "label_ru": "Волынская область", "macro": "west", "lat": 50.75, "lon": 25.34},
    {"id": "rivne", "label_ru": "Ровненская область", "macro": "west", "lat": 50.62, "lon": 26.25},
    {"id": "chernivtsi", "label_ru": "Черновицкая область", "macro": "west", "lat": 48.29, "lon": 25.94},
    {"id": "khmelnytskyi", "label_ru": "Хмельницкая область", "macro": "west", "lat": 49.42, "lon": 26.98},
    {"id": "zhytomyr", "label_ru": "Житомирская область", "macro": "north", "lat": 50.25, "lon": 28.66},
    {"id": "chernihiv", "label_ru": "Черниговская область", "macro": "north", "lat": 51.50, "lon": 31.29},
    {"id": "sumy", "label_ru": "Сумская область", "macro": "north", "lat": 50.91, "lon": 34.80},
    {"id": "kharkiv", "label_ru": "Харьковская область", "macro": "east", "lat": 49.99, "lon": 36.23},
    {"id": "dnipro", "label_ru": "Днепропетровская область", "macro": "east", "lat": 48.45, "lon": 35.04},
    {"id": "zaporizhzhia", "label_ru": "Запорожская область", "macro": "east", "lat": 47.84, "lon": 35.14},
    {"id": "donetsk", "label_ru": "Донецкая область", "macro": "east", "lat": 48.00, "lon": 37.80},
    {"id": "luhansk", "label_ru": "Луганская область", "macro": "east", "lat": 48.57, "lon": 39.31},
    {"id": "crimea", "label_ru": "Автономная Республика Крым", "macro": "south", "lat": 44.95, "lon": 34.10},
]

CROPS = [
    {"id": "wheat", "label_ru": "Пшеница", "matrix": "Wheat"},
    {"id": "corn", "label_ru": "Кукуруза", "matrix": "Corn"},
    {"id": "sunflower", "label_ru": "Подсолнечник", "matrix": "Sunflower"},
    {"id": "barley", "label_ru": "Ячмень", "matrix": "Barley"},
    {"id": "soy", "label_ru": "Соя", "matrix": "Soy"},
    {"id": "rapeseed", "label_ru": "Рапс", "matrix": "Rapeseed"},
]


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


def oblast_by_id(oblast_id: str) -> dict[str, Any] | None:
    return next((o for o in UA_OBLASTS if o["id"] == oblast_id), None)


def forecast_url(lat: float, lon: float, days: int = 7) -> str:
    horizon = max(1, min(int(days), 16))
    return (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,surface_pressure"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,weather_code"
        f"&forecast_days={horizon}&timezone=Europe%2FKyiv&wind_speed_unit=ms"
    )


def archive_url(lat: float, lon: float, start: str, end: str) -> str:
    return (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date={start}&end_date={end}"
        "&daily=temperature_2m_max,precipitation_sum&timezone=Europe%2FKyiv"
    )


def map_point(lat: float, lon: float) -> dict[str, float]:
    """Simple equirectangular projection over Ukraine bbox."""
    x = (lon - 22.0) / (40.2 - 22.0) * 800.0
    y = (52.5 - lat) / (52.5 - 44.3) * 480.0
    return {"x": round(max(8, min(792, x)), 1), "y": round(max(8, min(472, y)), 1)}


def _series_vals(rows: list[dict[str, Any]], metric: str) -> list[tuple[datetime, float]]:
    out: list[tuple[datetime, float]] = []
    aliases = {
        "tmax": ("tmax",),
        "tmin": ("tmin",),
        "precip": ("precip",),
        "humidity": ("humidity",),
        "wind": ("wind", "current_wind"),
        "pressure": ("pressure",),
        "precip_probability": ("precip_probability",),
        "weather_code": ("weather_code", "current_weather_code"),
        "current_temp": ("current_temp",),
        "soil_temp": ("soil_temp",),
    }
    wanted = aliases.get(metric, (metric,))
    for row in rows:
        unit = str(row.get("unit") or "")
        mid = str(row.get("metric") or "")
        sid = str(row.get("series_id") or "")
        if metric == "tmax":
            if mid:
                if mid != "tmax":
                    continue
            elif not (sid.endswith("-tmax") or (unit == "°C" and "tmax" in sid)):
                continue
        elif metric == "precip":
            if mid:
                if mid != "precip":
                    continue
            elif not (unit == "mm" or sid.endswith("-precip")):
                continue
        else:
            if mid not in wanted and not any(sid.endswith(f"-{a}") for a in wanted):
                continue
        ts = _parse_ts(row.get("observed_at") or row.get("published_at"))
        val = to_float(row.get("normalized_value") if row.get("normalized_value") is not None else row.get("value"))
        if ts is None or val is None:
            continue
        out.append((ts, val))
    out.sort(key=lambda x: x[0])
    return out


def crop_cell(crop_id: str, tmax_avg: float | None, precip_7: float | None) -> dict[str, Any]:
    if tmax_avg is None and precip_7 is None:
        return {
            "level": None,
            "label_en": "Missing",
            "label_ru": "Нет данных",
            "explanation_ru": MISSING_STATUS_RU,
            "missing": True,
        }
    tmax = tmax_avg if tmax_avg is not None else 0.0
    rain = precip_7 if precip_7 is not None else 0.0
    level = "Low"
    label_ru = "Низкий риск"
    why = "По доступному прогнозу экстремумов нет."
    if crop_id in {"corn", "sunflower", "soy"} and tmax >= 32 and rain < 12:
        level, label_ru = "High", "Высокий риск дефицита влаги"
        why = "Жара и мало осадков на горизонте 7 дней — стресс для теплолюбивых культур."
    elif crop_id in {"wheat", "barley", "rapeseed"} and rain >= 40:
        level, label_ru = "High", "Высокий риск избытка влаги"
        why = "Сумма осадков за 7 дней высокая — риск полегания и болезней."
    elif (tmax >= 30 and rain < 15) or rain >= 28:
        level, label_ru = "Medium", "Средний риск"
        why = "Условия отклоняются от комфортного диапазона, но не в зоне экстремума."
    return {
        "level": level,
        "label_en": level,
        "label_ru": label_ru,
        "explanation_ru": why,
        "missing": False,
    }


def region_narrative(macro_id: str, tmax_avg: float | None, precip_7: float | None, precip_30: float | None) -> dict[str, Any]:
    meta = next((m for m in MACRO_REGIONS if m["id"] == macro_id), MACRO_REGIONS[0])
    if tmax_avg is None and precip_7 is None:
        return {
            "macro_id": macro_id,
            "title_ru": meta["label_ru"],
            "next_7_ru": MISSING_STATUS_RU,
            "month_ru": MISSING_CLIMATE_RU,
            "risk_ru": "Риск не оценивается без наблюдений.",
            "impact_ru": "Влияние на культуры не рассчитывается.",
            "monitor_ru": "осадки, температуру, состояние посевов.",
            "missing": True,
        }
    if precip_7 is not None and precip_7 < 8 and (tmax_avg or 0) >= 28:
        next7 = "сухая и жаркая погода."
        risk = "повышенный риск дефицита влаги."
        impact = "кукуруза и подсолнечник могут испытывать стресс."
    elif precip_7 is not None and precip_7 >= 40:
        next7 = "влажная погода с существенными осадками."
        risk = "повышенный риск избытка влаги."
        impact = "пшеница и ячмень требуют контроля полегания."
    else:
        next7 = "умеренная погода по доступному прогнозу."
        risk = "умеренный операционный риск."
        impact = "существенного стресса по текущему ряду не видно."
    if precip_30 is None:
        month = MISSING_CLIMATE_RU
    elif precip_30 < 20:
        month = "осадки ниже недавнего наблюдаемого уровня."
    else:
        month = "осадки сопоставимы с недавним наблюдаемым уровнем."
    return {
        "macro_id": macro_id,
        "title_ru": meta["label_ru"],
        "next_7_ru": next7,
        "month_ru": month,
        "risk_ru": risk,
        "impact_ru": impact,
        "monitor_ru": "осадки, температуру почвы, состояние посевов.",
        "missing": False,
        "tmax_avg": tmax_avg,
        "precip_7": precip_7,
        "precip_30": precip_30,
    }


def history_compare(current: float | None, baseline: float | None, unit: str) -> dict[str, Any]:
    if current is None or baseline is None or not baseline:
        return {"ok": False, "text_ru": MISSING_CLIMATE_RU, "pct": None, "unit": unit}
    pct = round((current - baseline) / abs(baseline) * 100, 1)
    sign = "+" if pct > 0 else ""
    return {
        "ok": True,
        "pct": pct,
        "current": current,
        "baseline": baseline,
        "unit": unit,
        "text_ru": f"{sign}{pct}% относительно недавнего наблюдаемого уровня.",
    }


class AgroOpsWeatherMixin:
    """Mixed into AgroOpsService."""

    async def weather_dashboard(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        await self.ensure_weather_regions(org, role)
        rows = self._weather_rows(org)
        by_oblast: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            oid = str(row.get("oblast_id") or "")
            if oid:
                by_oblast[oid].append(row)
        oblast_summaries = []
        for spec in UA_OBLASTS:
            summary = self._oblast_summary(spec, by_oblast.get(spec["id"]) or [])
            oblast_summaries.append(summary)
        macros = []
        for macro in MACRO_REGIONS:
            members = [s for s in oblast_summaries if s["macro"] == macro["id"]]
            tmax = _avg([s.get("tmax_avg") for s in members])
            p7 = _avg([s.get("precip_7") for s in members])
            p30 = _avg([s.get("precip_30") for s in members])
            macros.append(region_narrative(macro["id"], tmax, p7, p30))
        crops_block = []
        for crop in CROPS:
            regions = []
            for macro in MACRO_REGIONS:
                members = [s for s in oblast_summaries if s["macro"] == macro["id"]]
                cell = crop_cell(crop["id"], _avg([s.get("tmax_avg") for s in members]), _avg([s.get("precip_7") for s in members]))
                regions.append({"macro_id": macro["id"], "short_ru": macro["short_ru"], **cell})
            crops_block.append({"id": crop["id"], "label_ru": crop["label_ru"], "regions": regions})
        matrix = {
            "columns": [{"id": c["id"], "label_en": c["matrix"], "label_ru": c["label_ru"]} for c in CROPS if c["id"] != "rapeseed"],
            "rows": [],
        }
        for macro in MACRO_REGIONS:
            members = [s for s in oblast_summaries if s["macro"] == macro["id"]]
            cells = {}
            for crop in CROPS:
                if crop["id"] == "rapeseed":
                    continue
                cells[crop["id"]] = crop_cell(
                    crop["id"],
                    _avg([s.get("tmax_avg") for s in members]),
                    _avg([s.get("precip_7") for s in members]),
                )
            matrix["rows"].append({"macro_id": macro["id"], "label_en": macro["short_ru"], "label_ru": macro["short_ru"], "cells": cells})
        history = self._weather_history_block(oblast_summaries)
        primary = next((p for p in (await self.providers_status(org, role)).get("items") or [] if p.get("id") == "weather_provider"), {})  # type: ignore[attr-defined]
        intel = self._weather_intel_payload(oblast_summaries, primary, crop_id=None)
        return {
            "ok": True,
            "macros": macros,
            "oblasts": oblast_summaries,
            "map": {
                "regions": [
                    {
                        **spec,
                        **map_point(spec["lat"], spec["lon"]),
                        "has_data": bool(by_oblast.get(spec["id"])),
                        "agro_risk": next((o.get("agro_risk") for o in oblast_summaries if o["id"] == spec["id"]), None),
                        "temperature": next((o.get("temperature") for o in oblast_summaries if o["id"] == spec["id"]), None),
                        "precip_7": next((o.get("precip_7") for o in oblast_summaries if o["id"] == spec["id"]), None),
                        "humidity": next((o.get("humidity") for o in oblast_summaries if o["id"] == spec["id"]), None),
                        "wind_speed": next((o.get("wind_speed") for o in oblast_summaries if o["id"] == spec["id"]), None),
                    }
                    for spec in UA_OBLASTS
                ]
            },
            "crops": crops_block,
            "matrix": matrix,
            "history": history,
            "provider": {
                "id": "weather_provider",
                "label_ru": primary.get("label_ru") or "Open-Meteo",
                "health_state": primary.get("health_state"),
                "health_color": primary.get("health_color"),
            },
            **intel,
        }

    def _weather_rows(self, org: str) -> list[dict[str, Any]]:
        from services.agro_ops.service import active_only

        bag = self._bag(org)  # type: ignore[attr-defined]
        rows = []
        for row in active_only(bag.get("weather_observation") or []):
            if row.get("is_demo") or str(row.get("data_class") or "") == "demo":
                continue
            rows.append(row)
        return rows

    def _oblast_summary(self, spec: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
        from services.agro_ops.weather_intel import agro_risk_from_metrics, weather_label_ru

        now = _now()
        tmax_pts = _series_vals(rows, "tmax")
        rain_pts = _series_vals(rows, "precip")
        tmin_pts = _series_vals(rows, "tmin")
        hum_pts = _series_vals(rows, "humidity")
        wind_pts = _series_vals(rows, "wind")
        pres_pts = _series_vals(rows, "pressure")
        prob_pts = _series_vals(rows, "precip_probability")
        code_pts = _series_vals(rows, "weather_code")
        cur_pts = _series_vals(rows, "current_temp")
        soil_pts = _series_vals(rows, "soil_temp")
        next7 = now + timedelta(days=7)
        cut30 = now - timedelta(days=30)
        tmax_7 = [v for ts, v in tmax_pts if now - timedelta(hours=12) <= ts <= next7 or ts >= now - timedelta(days=1)]
        if not tmax_7:
            tmax_7 = [v for ts, v in tmax_pts[-7:]]
        rain_7 = [v for ts, v in rain_pts if ts >= now - timedelta(days=1)]
        if len(rain_7) < 2:
            rain_7 = [v for _, v in rain_pts[-7:]]
        rain_30 = [v for ts, v in rain_pts if ts >= cut30]
        tmax_now = (cur_pts[-1][1] if cur_pts else None) or (tmax_pts[-1][1] if tmax_pts else None)
        rain_now = rain_pts[-1][1] if rain_pts else None
        by_day: dict[str, dict[str, Any]] = {}
        for key, pts in (
            ("tmax", tmax_pts[-16:]),
            ("tmin", tmin_pts[-16:]),
            ("precip", rain_pts[-16:]),
            ("precip_probability", prob_pts[-16:]),
            ("wind", wind_pts[-16:]),
            ("weather_code", code_pts[-16:]),
        ):
            for ts, v in pts:
                by_day.setdefault(ts.date().isoformat(), {})[key] = v
        forecast = []
        for day, vals in sorted(by_day.items())[-16:]:
            forecast.append(
                {
                    "date": day,
                    "tmax": vals.get("tmax"),
                    "tmin": vals.get("tmin"),
                    "precip": vals.get("precip"),
                    "precip_probability": vals.get("precip_probability"),
                    "wind": _wind_ms(vals.get("wind")),
                    "weather_code": int(vals["weather_code"]) if vals.get("weather_code") is not None else None,
                    "weather_ru": weather_label_ru(int(vals["weather_code"]) if vals.get("weather_code") is not None else None),
                }
            )
        today_iso = now.date().isoformat()
        upcoming = [d for d in forecast if str(d.get("date") or "") >= today_iso]
        forecast_7 = (upcoming or forecast)[:7]
        humidity = hum_pts[-1][1] if hum_pts else None
        wind = _wind_ms(wind_pts[-1][1] if wind_pts else None)
        pressure = pres_pts[-1][1] if pres_pts else None
        weather_code = int(code_pts[-1][1]) if code_pts else None
        tmin_now = tmin_pts[0][1] if tmin_pts else None
        soil = soil_pts[-1][1] if soil_pts else None
        precip_7 = round(sum(rain_7), 1) if rain_7 else None
        tmax_avg = _avg(tmax_7) if tmax_7 else None
        risk = agro_risk_from_metrics(tmax=tmax_avg, precip_7=precip_7, humidity=humidity, wind=wind, tmin=tmin_now)
        missing = not tmax_pts and not rain_pts
        latest_ts = None
        for pts in (cur_pts, hum_pts, tmax_pts, rain_pts):
            for ts, _v in reversed(pts):
                if ts <= now + timedelta(hours=3):
                    latest_ts = ts if latest_ts is None or ts > latest_ts else latest_ts
                    break
        if latest_ts is None and (tmax_pts or rain_pts or cur_pts):
            latest_ts = now
        return {
            "id": spec["id"],
            "label_ru": spec["label_ru"],
            "macro": spec["macro"],
            "lat": spec["lat"],
            "lon": spec["lon"],
            "coordinates": {"lat": spec["lat"], "lon": spec["lon"]},
            "temperature": tmax_now,
            "rain": rain_now,
            "tmax_avg": tmax_avg,
            "tmin": tmin_now,
            "precip_7": precip_7,
            "precip_30": sum(rain_30) if len(rain_30) >= 10 else None,
            "humidity": humidity,
            "wind_speed": wind,
            "pressure": pressure,
            "precip_probability": prob_pts[-1][1] if prob_pts else None,
            "weather_code": weather_code,
            "weather_ru": weather_label_ru(weather_code),
            "soil_temperature": soil,
            "forecast_7": forecast_7,
            "forecast": forecast,
            "current": {
                "temperature": tmax_now,
                "humidity": humidity,
                "precipitation": rain_now,
                "wind_speed": wind,
                "pressure": pressure,
                "weather_code": weather_code,
                "weather_ru": weather_label_ru(weather_code),
                "soil_temperature": soil,
                "precip_probability": prob_pts[-1][1] if prob_pts else None,
            },
            "agro_risk": risk,
            "missing": missing,
            "status_ru": MISSING_STATUS_RU if missing else None,
            "source": "weather_provider",
            "updated_at": latest_ts.isoformat() if latest_ts else None,
        }

    def _weather_history_block(self, oblasts: list[dict[str, Any]]) -> dict[str, Any]:
        p7 = _avg([s.get("precip_7") for s in oblasts])
        p30 = _avg([s.get("precip_30") for s in oblasts])
        return {
            "today": {"ok": any(s.get("temperature") is not None for s in oblasts)},
            "days_7": {"precip": p7, "text_ru": None if p7 is not None else MISSING_STATUS_RU},
            "days_30": {
                "precip": p30,
                "text_ru": MISSING_CLIMATE_RU,
            },
            "season": {"text_ru": MISSING_CLIMATE_RU},
            "note_ru": MISSING_CLIMATE_RU,
        }

    async def weather_region(self, organization_id: str, oblast_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        spec = oblast_by_id(oblast_id)
        if not spec:
            return {"ok": False, "error": "not_found", "message_ru": "Область не найдена"}
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        await self._fetch_oblast_weather(org, spec, role)
        dash = await self.weather_dashboard(org, role)
        item = next((o for o in dash.get("oblasts") or [] if o.get("id") == oblast_id), None)
        crop_impact = [
            {"crop_id": c["id"], "crop_ru": c["label_ru"], **crop_cell(c["id"], (item or {}).get("tmax_avg"), (item or {}).get("precip_7"))}
            for c in CROPS
        ]
        return {
            "ok": True,
            "item": item,
            "forecast_7": (item or {}).get("forecast_7") or [],
            "forecast": (item or {}).get("forecast") or [],
            "monthly_outlook_ru": MISSING_CLIMATE_RU if not (item or {}).get("precip_30") else "Осадки за 30 дней посчитаны по сохранённым наблюдениям, без климатической нормы.",
            "outlook_30d": self._outlook_for_item(item),
            "risk": crop_cell("corn", (item or {}).get("tmax_avg"), (item or {}).get("precip_7")),
            "agro_risk": (item or {}).get("agro_risk"),
            "crop_impact": crop_impact,
            "recommendations": self._recs_for_item(item, None),
            "confidence": dash.get("confidence"),
            "last_updated": dash.get("last_updated"),
            "fallback": dash.get("fallback"),
        }

    async def ensure_weather_regions(self, org: str, role: str | None) -> None:
        have = {str(r.get("oblast_id") or "") for r in self._weather_rows(org)}
        needed = [s for s in UA_OBLASTS if s["id"] not in have]
        # First paint: fetch a representative set so the map is live without 24 serial calls.
        if len(have) < 5:
            needed = [oblast_by_id("odesa"), oblast_by_id("lviv"), oblast_by_id("kyiv"), oblast_by_id("kharkiv"), oblast_by_id("chernihiv")]
            needed = [s for s in needed if s]
        for spec in needed[:8]:
            try:
                await self._fetch_oblast_weather(org, spec, role)
            except Exception:
                continue

    async def _fetch_oblast_weather(self, org: str, spec: dict[str, Any], role: str | None) -> dict[str, Any]:
        url = forecast_url(spec["lat"], spec["lon"], 16)
        fetched = await self._fetch_url(url, {"id": "weather_provider", "url": url})  # type: ignore[attr-defined]
        if fetched.unavailable or fetched.timed_out or (fetched.status and fetched.status >= 400) or not fetched.text:
            return {"ok": False, "oblast_id": spec["id"]}
        rows = parse_open_meteo(
            fetched.text,
            "weather_provider",
            url,
            region=spec["label_ru"],
            oblast_id=spec["id"],
            macro_region=spec["macro"],
        )
        existing = {(r.get("series_id"), str(r.get("observed_at") or "")[:10]) for r in self._weather_rows(org) if r.get("oblast_id") == spec["id"]}
        stored = 0
        for row in rows:
            key = (row.get("series_id"), str(row.get("observed_at") or "")[:10])
            if key in existing:
                continue
            payload = {
                **row,
                "name": row.get("title"),
                "oblast_id": spec["id"],
                "macro_region": spec["macro"],
                "region": spec["label_ru"],
            }
            await self.create_entity(org, "weather_observation", payload, role or "platform_owner")  # type: ignore[attr-defined]
            stored += 1
        return {"ok": True, "oblast_id": spec["id"], "count": stored, "fetched": True}

    def _outlook_for_item(self, item: dict[str, Any] | None) -> dict[str, Any]:
        from services.agro_ops.weather_intel import outlook_30d_from_series

        row = item or {}
        return outlook_30d_from_series(
            forecast_days=row.get("forecast") or row.get("forecast_7") or [],
            precip_30=row.get("precip_30"),
            tmax_avg=row.get("tmax_avg"),
            precip_7=row.get("precip_7"),
        )

    def _recs_for_item(self, item: dict[str, Any] | None, crop_id: str | None) -> list[dict[str, Any]]:
        from services.agro_ops.weather_intel import recommendations_from_forecast

        row = item or {}
        return recommendations_from_forecast(
            row.get("forecast_7") or row.get("forecast") or [],
            tmax_avg=row.get("tmax_avg"),
            precip_7=row.get("precip_7"),
            humidity=row.get("humidity"),
            wind=row.get("wind_speed"),
            crop_id=crop_id,
        )

    def _weather_intel_payload(
        self,
        oblast_summaries: list[dict[str, Any]],
        primary: dict[str, Any],
        crop_id: str | None = None,
    ) -> dict[str, Any]:
        from services.agro_ops.weather_intel import (
            calendar_from_recommendations,
            confidence_from_context,
            format_last_updated,
            recommendations_from_forecast,
            region_card,
            resolve_crop_id,
        )

        crop = resolve_crop_id(crop_id)
        stamps = [_parse_ts(o.get("updated_at")) for o in oblast_summaries]
        latest = max([s for s in stamps if s], default=None)
        last = format_last_updated(latest)
        present: list[str] = []
        if any(o.get("temperature") is not None for o in oblast_summaries):
            present.append("temperature")
        if any(o.get("precip_7") is not None for o in oblast_summaries):
            present.append("precipitation")
        if any(o.get("humidity") is not None for o in oblast_summaries):
            present.append("humidity")
        if any(o.get("wind_speed") is not None for o in oblast_summaries):
            present.append("wind_speed")
        if any(o.get("pressure") is not None for o in oblast_summaries):
            present.append("pressure")
        if any(o.get("tmin") is not None for o in oblast_summaries):
            present.append("tmin")
        if any(o.get("precip_probability") is not None for o in oblast_summaries):
            present.append("precip_probability")
        health = str(primary.get("health_state") or "")
        has_data = any(not o.get("missing") for o in oblast_summaries)
        sources_count = 1 if health == "CONNECTED" or has_data else 0
        conf = confidence_from_context(
            sources_count=sources_count,
            freshness_hours=last.get("hours"),
            health_state=health,
            present_metrics=present,
        )
        stale = bool(has_data and health in {"FAILED", "BLOCKED", "TIMEOUT", "UNAVAILABLE"})
        fallback = None
        if stale:
            fallback = {
                "used": True,
                "last_success_at": last.get("iso"),
                "message_ru": (
                    "Свежие погодные данные временно недоступны. "
                    f"Показаны последние успешно полученные данные: {last.get('display_ru') or '—'}"
                ),
            }
        elif not has_data:
            fallback = {
                "used": False,
                "message_ru": "Свежие погодные данные временно недоступны.",
            }
        region_cards = [region_card(m["id"], [s for s in oblast_summaries if s.get("macro") == m["id"]]) for m in MACRO_REGIONS]
        # National recs from averaged south+center members if present, else all
        seed = next((s for s in oblast_summaries if not s.get("missing")), oblast_summaries[0] if oblast_summaries else {})
        recs = recommendations_from_forecast(
            seed.get("forecast_7") or [],
            tmax_avg=seed.get("tmax_avg"),
            precip_7=seed.get("precip_7"),
            humidity=seed.get("humidity"),
            wind=seed.get("wind_speed"),
            crop_id=crop,
        )
        outlook = self._outlook_for_item(seed)
        return {
            "last_updated": last,
            "confidence": {**conf, "freshness": last.get("iso")},
            "recommendations": recs,
            "calendar": calendar_from_recommendations(recs),
            "region_cards": region_cards,
            "outlook_30d": outlook,
            "fallback": fallback,
            "crop": {"id": crop, "label_ru": next((c["label_ru"] for c in CROPS if c["id"] == crop), "Общий обзор")},
            "sources": [
                {
                    "id": "weather_provider",
                    "label_ru": primary.get("label_ru") or "Open-Meteo",
                    "health_state": health or None,
                }
            ],
        }

    def _pick_scope_item(self, dash: dict[str, Any], scope: str | None) -> dict[str, Any] | None:
        from services.agro_ops.weather_intel import oblast_ids_for_scope, region_card

        key = str(scope or "").strip().lower()
        oblasts = dash.get("oblasts") or []
        if not key:
            return next((o for o in oblasts if not o.get("missing")), oblasts[0] if oblasts else None)
        found = next((o for o in oblasts if o.get("id") == key), None)
        if found:
            return found
        if any(m["id"] == key for m in MACRO_REGIONS):
            members = [o for o in oblasts if o.get("macro") == key]
            card = region_card(key, members)
            seed = next((o for o in members if not o.get("missing")), members[0] if members else {})
            return {
                **(seed or {}),
                "id": key,
                "label_ru": card.get("title_ru"),
                "macro": key,
                "temperature": card.get("temperature"),
                "tmax_avg": card.get("temperature"),
                "precip_7": card.get("precip_7"),
                "humidity": card.get("humidity"),
                "wind_speed": card.get("wind_speed"),
                "agro_risk": card.get("agro_risk"),
                "is_macro": True,
            }
        ids = oblast_ids_for_scope(key)
        if ids:
            return next((o for o in oblasts if o.get("id") in ids), None)
        return None

    async def weather_overview(self, organization_id: str, role: str | None = None, crop: str | None = None) -> dict[str, Any]:
        dash = await self.weather_dashboard(organization_id, role)
        if not dash.get("ok"):
            return dash
        from services.agro_ops.weather_intel import resolve_crop_id

        crop_id = resolve_crop_id(crop)
        if crop_id:
            intel = self._weather_intel_payload(dash.get("oblasts") or [], dash.get("provider") or {}, crop_id=crop_id)
            dash.update(intel)
        return dash

    async def weather_regions_index(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        dash = await self.weather_dashboard(organization_id, role)
        if not dash.get("ok"):
            return dash
        return {
            "ok": True,
            "items": dash.get("region_cards") or [],
            "macros": dash.get("macros") or [],
            "last_updated": dash.get("last_updated"),
            "confidence": dash.get("confidence"),
        }

    async def weather_oblast(self, organization_id: str, oblast_id: str, role: str | None = None, crop: str | None = None) -> dict[str, Any]:
        from services.agro_ops.weather_intel import resolve_crop_id

        result = await self.weather_region(organization_id, oblast_id, role)
        if not result.get("ok"):
            return result
        crop_id = resolve_crop_id(crop)
        if crop_id:
            result["recommendations"] = self._recs_for_item(result.get("item"), crop_id)
            result["agro_risk"] = (result.get("item") or {}).get("agro_risk")
        return result

    async def weather_forecast(self, organization_id: str, role: str | None = None, region: str | None = None, days: int = 7) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        dash = await self.weather_dashboard(organization_id, role)
        if not dash.get("ok"):
            return dash
        item = self._pick_scope_item(dash, region)
        horizon = max(1, min(int(days or 7), 16))
        series = ((item or {}).get("forecast") or (item or {}).get("forecast_7") or [])[:horizon]
        return {
            "ok": True,
            "region": region,
            "item": item,
            "days": horizon,
            "forecast": series,
            "last_updated": dash.get("last_updated"),
            "fallback": dash.get("fallback"),
        }

    async def weather_outlook(self, organization_id: str, role: str | None = None, region: str | None = None, days: int = 30) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        dash = await self.weather_dashboard(organization_id, role)
        if not dash.get("ok"):
            return dash
        item = self._pick_scope_item(dash, region)
        outlook = self._outlook_for_item(item)
        return {
            "ok": True,
            "region": region,
            "days": days,
            "item": item,
            "outlook_30d": outlook,
            "monthly_outlook_ru": MISSING_CLIMATE_RU if not (item or {}).get("precip_30") else "Осадки за 30 дней посчитаны по сохранённым наблюдениям, без климатической нормы.",
            "confidence": dash.get("confidence"),
        }

    async def weather_agro_risk(self, organization_id: str, role: str | None = None, region: str | None = None, crop: str | None = None) -> dict[str, Any]:
        from services.agro_ops.weather_intel import agro_risk_from_metrics, resolve_crop_id

        denied = require(role, "list")
        if denied:
            return denied
        dash = await self.weather_dashboard(organization_id, role)
        if not dash.get("ok"):
            return dash
        item = self._pick_scope_item(dash, region)
        crop_id = resolve_crop_id(crop)
        row = item or {}
        risk = agro_risk_from_metrics(
            tmax=row.get("tmax_avg"),
            precip_7=row.get("precip_7"),
            humidity=row.get("humidity"),
            wind=row.get("wind_speed"),
            tmin=row.get("tmin"),
            crop_id=crop_id,
        )
        return {"ok": True, "region": region, "crop": crop_id, "item": item, "agro_risk": risk}

    async def weather_recommendations(self, organization_id: str, role: str | None = None, region: str | None = None, crop: str | None = None) -> dict[str, Any]:
        from services.agro_ops.weather_intel import calendar_from_recommendations, resolve_crop_id

        denied = require(role, "list")
        if denied:
            return denied
        dash = await self.weather_dashboard(organization_id, role)
        if not dash.get("ok"):
            return dash
        item = self._pick_scope_item(dash, region)
        crop_id = resolve_crop_id(crop)
        recs = self._recs_for_item(item, crop_id)
        return {
            "ok": True,
            "region": region,
            "crop": crop_id,
            "general": crop_id is None,
            "recommendations": recs,
            "calendar": calendar_from_recommendations(recs),
        }

    async def weather_refresh(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        fetched = 0
        failed = 0
        last_ok = None
        wanted_ids = ["odesa", "lviv", "kyiv", "kharkiv", "chernihiv", "dnipro", "mykolaiv", "zhytomyr"]
        have = {str(r.get("oblast_id") or "") for r in self._weather_rows(org)}
        specs = [s for s in (oblast_by_id(i) for i in wanted_ids) if s]
        extra = [s for s in UA_OBLASTS if s["id"] in have and s["id"] not in wanted_ids]
        for spec in [*specs, *extra][:12]:
            try:
                result = await self._fetch_oblast_weather(org, spec, role)
                if result.get("ok"):
                    fetched += 1
                    last_ok = spec["id"]
                else:
                    failed += 1
            except Exception:
                failed += 1
        dash = await self.weather_dashboard(org, role)
        return {
            "ok": fetched > 0 or bool(dash.get("oblasts")),
            "refreshed": fetched,
            "failed": failed,
            "last_ok": last_ok,
            "last_updated": dash.get("last_updated"),
            "fallback": dash.get("fallback"),
            "dashboard": dash,
        }


def _avg(values: list[Any]) -> float | None:
    nums = [float(v) for v in values if v is not None]
    if not nums:
        return None
    return round(sum(nums) / len(nums), 2)


def _wind_ms(value: Any) -> float | None:
    """Open-Meteo default wind is km/h unless wind_speed_unit=ms. Convert obvious km/h."""
    if value is None:
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if num > 18:
        return round(num / 3.6, 1)
    return round(num, 1)
