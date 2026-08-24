"""AGRO Weather Intelligence — risk, confidence, outlook, recommendations.

All values must come from stored/normalized observations. Missing metrics stay None.
Never invent climate normals, soil temperature, or a day-by-day 30-day forecast.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.agro_ops.weather import CROPS, MACRO_REGIONS, UA_OBLASTS, crop_cell, history_compare

MISSING_OUTLOOK_RU = "Недостаточно данных для уверенного прогноза."
GENERAL_INDICATOR_RU = "Общий погодный агро-индикатор — культура не выбрана."
CROP_CONTEXT_RU = "Рекомендации учитывают выбранную культуру. Фаза роста и тип почвы пока не подключены."

WMO_WEATHER_RU = {
    0: "Ясно",
    1: "Преимущественно ясно",
    2: "Переменная облачность",
    3: "Пасмурно",
    45: "Туман",
    48: "Туман с изморозью",
    51: "Морось",
    53: "Морось",
    55: "Сильная морось",
    61: "Небольшой дождь",
    63: "Дождь",
    65: "Сильный дождь",
    71: "Небольшой снег",
    73: "Снег",
    75: "Сильный снег",
    80: "Ливень",
    81: "Ливень",
    82: "Сильный ливень",
    95: "Гроза",
    96: "Гроза с градом",
    99: "Гроза с градом",
}

CROP_NAME_TO_ID = {
    "wheat": "wheat",
    "пшеница": "wheat",
    "corn": "corn",
    "кукуруза": "corn",
    "sunflower": "sunflower",
    "подсолнечник": "sunflower",
    "barley": "barley",
    "ячмень": "barley",
    "soy": "soy",
    "соя": "soy",
    "rapeseed": "rapeseed",
    "рапс": "rapeseed",
}

WORK_KINDS = [
    {"id": "harvest", "category_ru": "Сбор урожая", "icon": "🌾"},
    {"id": "machinery", "category_ru": "Вывоз техники", "icon": "🚜"},
    {"id": "spraying", "category_ru": "Опрыскивание", "icon": "🧪"},
    {"id": "fertilizer", "category_ru": "Внесение удобрений", "icon": "🧂"},
    {"id": "irrigation", "category_ru": "Полив", "icon": "💧"},
    {"id": "sowing", "category_ru": "Посев", "icon": "🌱"},
    {"id": "tillage", "category_ru": "Обработка почвы", "icon": "🧱"},
    {"id": "plant_protection", "category_ru": "Защита растений", "icon": "🛡"},
]


def weather_label_ru(code: int | None) -> str | None:
    if code is None:
        return None
    return WMO_WEATHER_RU.get(int(code), "Сложные условия")


def resolve_crop_id(raw: str | None) -> str | None:
    key = str(raw or "").strip().lower()
    if not key or key in {"general", "общий", "общий обзор", "*"}:
        return None
    if key in CROP_NAME_TO_ID:
        return CROP_NAME_TO_ID[key]
    for crop in CROPS:
        if crop["id"] == key or str(crop["label_ru"]).lower() == key:
            return str(crop["id"])
    return None


def crop_label_ru(crop_id: str | None) -> str:
    if not crop_id:
        return "Общий обзор"
    found = next((c for c in CROPS if c["id"] == crop_id), None)
    return str(found["label_ru"]) if found else crop_id


def macro_meta(macro_id: str) -> dict[str, Any]:
    found = next((m for m in MACRO_REGIONS if m["id"] == macro_id), None)
    titles = {
        "south": ("ЮЖНЫЙ РЕГИОН", "ПІВДЕННИЙ РЕГІОН", "Южный"),
        "center": ("ЦЕНТРАЛЬНЫЙ РЕГИОН", "ЦЕНТРАЛЬНИЙ РЕГІОН", "Центральный"),
        "west": ("ЗАПАДНЫЙ РЕГИОН", "ЗАХІДНИЙ РЕГІОН", "Западный"),
        "north": ("СЕВЕРНЫЙ РЕГИОН", "ПІВНІЧНИЙ РЕГІОН", "Северный"),
        "east": ("ВОСТОЧНЫЙ РЕГИОН", "СХІДНИЙ РЕГІОН", "Восточный"),
    }
    ru, uk, short = titles.get(macro_id, ("РЕГИОН", "РЕГІОН", macro_id))
    return {
        "id": macro_id,
        "label_ru": (found or {}).get("label_ru") or ru,
        "short_ru": (found or {}).get("short_ru") or short,
        "title_full_ru": ru,
        "title_uk": uk,
        "title_card_ru": short.upper(),
    }


def oblast_ids_for_scope(scope: str | None) -> list[str]:
    key = str(scope or "").strip().lower()
    if not key or key in {"ua", "ukraine", "all"}:
        return [str(o["id"]) for o in UA_OBLASTS]
    if any(m["id"] == key for m in MACRO_REGIONS):
        return [str(o["id"]) for o in UA_OBLASTS if o["macro"] == key]
    if any(o["id"] == key for o in UA_OBLASTS):
        return [key]
    return []


def _level_from_score(score: int) -> str:
    if score >= 75:
        return "High"
    if score >= 45:
        return "Medium"
    return "Low"


def agro_risk_from_metrics(
    *,
    tmax: float | None,
    precip_7: float | None,
    humidity: float | None = None,
    wind: float | None = None,
    tmin: float | None = None,
    crop_id: str | None = None,
) -> dict[str, Any]:
    """Operational agro-risk from available metrics only."""
    if tmax is None and precip_7 is None and humidity is None and tmin is None:
        return {
            "level": None,
            "score": None,
            "label_en": "Missing",
            "label_ru": "Нет данных",
            "reasons": ["Нет актуальных погодных данных по этому региону."],
            "missing": True,
        }
    score = 15
    reasons: list[str] = []
    if tmax is not None and tmax >= 34:
        score += 40
        reasons.append("Жара: температура на горизонте 7 дней высокая.")
    elif tmax is not None and tmax >= 30:
        score += 22
        reasons.append("Тепло выше комфортного диапазона.")
    if precip_7 is not None and precip_7 < 5 and (tmax or 0) >= 28:
        score += 28
        reasons.append("Дефицит осадков на фоне тепла — риск засухи.")
    elif precip_7 is not None and precip_7 < 8:
        score += 16
        reasons.append("Осадки за 7 дней низкие.")
    elif precip_7 is not None and precip_7 >= 40:
        score += 28
        reasons.append("Избыток осадков — риск полегания и болезней.")
    elif precip_7 is not None and precip_7 >= 28:
        score += 14
        reasons.append("Осадки выше комфортного диапазона.")
    if humidity is not None and humidity < 35 and (precip_7 is None or precip_7 < 12):
        score += 12
        reasons.append("Низкая влажность воздуха.")
    if wind is not None and wind >= 10:
        score += 8
        reasons.append("Сильный ветер ограничивает опрыскивание и вывоз.")
    if tmin is not None and tmin <= 2:
        score += 18
        reasons.append("Близкие к нулю ночные температуры — риск заморозков.")
    if crop_id:
        cell = crop_cell(crop_id, tmax, precip_7)
        if cell.get("level") == "High":
            score = max(score, 80)
            reasons.append(str(cell.get("explanation_ru") or ""))
        elif cell.get("level") == "Medium":
            score = max(score, 50)
    score = min(100, score)
    level = _level_from_score(score)
    labels = {"High": "Высокий", "Medium": "Умеренный", "Low": "Низкий"}
    if not reasons:
        reasons.append("По доступному прогнозу экстремумов нет.")
    return {
        "level": level,
        "score": score,
        "label_en": level,
        "label_ru": labels[level],
        "reasons": [r for r in reasons if r],
        "missing": False,
        "drought": bool(precip_7 is not None and precip_7 < 8 and (tmax or 0) >= 28),
        "frost": bool(tmin is not None and tmin <= 2),
        "heat": bool(tmax is not None and tmax >= 32),
        "excess_rain": bool(precip_7 is not None and precip_7 >= 40),
    }


def confidence_from_context(
    *,
    sources_count: int,
    freshness_hours: float | None,
    health_state: str | None,
    present_metrics: list[str],
    required_metrics: tuple[str, ...] = ("temperature", "precipitation"),
    source_agreement: float | None = None,
) -> dict[str, Any]:
    sources = max(0, int(sources_count))
    completeness = 0.0
    if required_metrics:
        hit = sum(1 for m in required_metrics if m in present_metrics)
        extra = ["humidity", "wind_speed", "pressure", "tmin", "precip_probability"]
        extra_hit = sum(1 for m in extra if m in present_metrics)
        completeness = (hit / len(required_metrics)) * 0.7 + (extra_hit / len(extra)) * 0.3
    score = 0
    if sources >= 1:
        score += 40
    if freshness_hours is not None and freshness_hours <= 24:
        score += 25
    elif freshness_hours is not None and freshness_hours <= 72:
        score += 12
    score += int(round(20 * completeness))
    health = str(health_state or "").upper()
    if health == "CONNECTED":
        score += 15
    elif health in {"PARTIAL", "DEGRADED"}:
        score += 6
    if source_agreement is not None:
        score = int(round(score * (0.7 + 0.3 * max(0.0, min(1.0, source_agreement)))))
    elif sources <= 1:
        # One live source: cannot measure disagreement. Do not pretend otherwise.
        score = min(score, 82)
    score = max(0, min(100, score))
    if score >= 70:
        label_ru, label_en = "ВЫСОКИЙ", "HIGH"
    elif score >= 40:
        label_ru, label_en = "СРЕДНИЙ", "MEDIUM"
    else:
        label_ru, label_en = "НИЗКИЙ", "LOW"
    noun = "источника" if sources == 1 else "источников"
    return {
        "score": score,
        "label_ru": label_ru,
        "label_en": label_en,
        "sources_count": sources,
        "freshness_hours": round(freshness_hours, 1) if freshness_hours is not None else None,
        "health_state": health or None,
        "completeness": round(completeness, 2),
        "agreement": source_agreement,
        "text_ru": f"Прогноз основан на данных {sources} {noun}",
        "note_ru": None if sources != 1 else "Доступен один рабочий источник погоды.",
    }


def outlook_30d_from_series(
    *,
    forecast_days: list[dict[str, Any]],
    precip_30: float | None,
    tmax_avg: float | None,
    precip_7: float | None,
) -> dict[str, Any]:
    """Analytical 30-day outlook. Not a fake daily forecast.

    Open-Meteo free forecast is at most 16 days. Climate normals are never invented.
    """
    horizon = len(forecast_days)
    if horizon < 5 and precip_30 is None and tmax_avg is None:
        return {
            "available": False,
            "horizon_days": horizon,
            "text_ru": MISSING_OUTLOOK_RU,
            "temperature_trend": {"ok": False, "text_ru": MISSING_OUTLOOK_RU},
            "precipitation_trend": {"ok": False, "text_ru": MISSING_OUTLOOK_RU},
            "drought_probability": {"ok": False, "text_ru": MISSING_OUTLOOK_RU},
            "excessive_rain_probability": {"ok": False, "text_ru": MISSING_OUTLOOK_RU},
            "heat_probability": {"ok": False, "text_ru": MISSING_OUTLOOK_RU},
            "frost_probability": {"ok": False, "text_ru": MISSING_OUTLOOK_RU},
            "moisture": {"ok": False, "text_ru": MISSING_OUTLOOK_RU},
            "agro_risk": {"ok": False, "text_ru": MISSING_OUTLOOK_RU},
        }
    tmax_vals = [d.get("tmax") for d in forecast_days if d.get("tmax") is not None]
    tmin_vals = [d.get("tmin") for d in forecast_days if d.get("tmin") is not None]
    rain_vals = [d.get("precip") for d in forecast_days if d.get("precip") is not None]
    mean_tmax = round(sum(tmax_vals) / len(tmax_vals), 1) if tmax_vals else tmax_avg
    sum_rain = round(sum(rain_vals), 1) if rain_vals else precip_7
    later = tmax_vals[7:] if len(tmax_vals) > 8 else []
    early = tmax_vals[:7] if len(tmax_vals) >= 7 else tmax_vals
    if later and early:
        delta = round((sum(later) / len(later)) - (sum(early) / len(early)), 1)
        if delta >= 1.5:
            t_text = f"во второй половине горизонта вероятнее теплее примерно на {abs(delta):.1f}°C относительно ближайших дней."
        elif delta <= -1.5:
            t_text = f"во второй половине горизонта вероятнее прохладнее примерно на {abs(delta):.1f}°C относительно ближайших дней."
        else:
            t_text = "температурный фон на доступном горизонте без резкого сдвига."
        t_block = {"ok": True, "delta_c": delta, "text_ru": t_text, "mean_tmax": mean_tmax}
    elif mean_tmax is not None:
        t_block = {
            "ok": True,
            "delta_c": None,
            "mean_tmax": mean_tmax,
            "text_ru": f"Средняя максимальная температура по доступному прогнозу: {mean_tmax}°C. Сравнения с климатической нормой нет.",
        }
    else:
        t_block = {"ok": False, "text_ru": MISSING_OUTLOOK_RU}

    baseline = history_compare(sum_rain, precip_30, "mm") if sum_rain is not None else {"ok": False, "text_ru": MISSING_OUTLOOK_RU}
    if baseline.get("ok"):
        pct = float(baseline.get("pct") or 0)
        if pct <= -20:
            p_text = "осадки, вероятно, ниже недавнего наблюдаемого уровня."
        elif pct >= 20:
            p_text = "осадки, вероятно, выше недавнего наблюдаемого уровня."
        else:
            p_text = "осадки сопоставимы с недавним наблюдаемым уровнем."
        p_block = {"ok": True, "text_ru": p_text, "pct": pct}
    else:
        p_block = {
            "ok": False if sum_rain is None else True,
            "text_ru": MISSING_OUTLOOK_RU if sum_rain is None else f"Сумма осадков на доступном горизонте: {sum_rain} мм. Климатической нормы нет.",
            "sum_mm": sum_rain,
        }

    drought_on = bool(sum_rain is not None and sum_rain < 12 and (mean_tmax or 0) >= 28)
    rain_on = bool(sum_rain is not None and sum_rain >= 45)
    heat_on = bool(mean_tmax is not None and mean_tmax >= 32)
    frost_on = bool(tmin_vals and min(tmin_vals) <= 2)
    risk = agro_risk_from_metrics(tmax=mean_tmax, precip_7=sum_rain, tmin=min(tmin_vals) if tmin_vals else None)
    return {
        "available": True,
        "horizon_days": horizon,
        "provider_horizon_note_ru": (
            f"Достоверный суточный прогноз доступен на {horizon} дн. "
            "30-дневный блок — агрегированная оценка по этому ряду, без климатической нормы."
            if horizon
            else MISSING_OUTLOOK_RU
        ),
        "temperature_trend": t_block,
        "precipitation_trend": p_block,
        "drought_probability": {
            "ok": sum_rain is not None,
            "level": "elevated" if drought_on else ("low" if sum_rain is not None else None),
            "text_ru": "повышенная вероятность" if drought_on else ("низкая по доступному ряду" if sum_rain is not None else MISSING_OUTLOOK_RU),
        },
        "excessive_rain_probability": {
            "ok": sum_rain is not None,
            "level": "elevated" if rain_on else ("low" if sum_rain is not None else None),
            "text_ru": "повышенная вероятность продолжительных дождей" if rain_on else ("низкая по доступному ряду" if sum_rain is not None else MISSING_OUTLOOK_RU),
        },
        "heat_probability": {
            "ok": mean_tmax is not None,
            "level": "elevated" if heat_on else ("low" if mean_tmax is not None else None),
            "text_ru": "повышенный риск жары" if heat_on else ("умеренный" if mean_tmax is not None else MISSING_OUTLOOK_RU),
        },
        "frost_probability": {
            "ok": bool(tmin_vals),
            "level": "elevated" if frost_on else ("low" if tmin_vals else None),
            "text_ru": "есть риск заморозков" if frost_on else ("по доступному минимуму не видно" if tmin_vals else MISSING_OUTLOOK_RU),
        },
        "moisture": {
            "ok": sum_rain is not None,
            "text_ru": (
                "дефицит влаги"
                if drought_on
                else ("избыток влаги" if rain_on else ("в пределах доступного ряда" if sum_rain is not None else MISSING_OUTLOOK_RU))
            ),
        },
        "agro_risk": {
            "ok": not risk.get("missing"),
            "level": risk.get("level"),
            "label_ru": str(risk.get("label_ru") or "").upper() if risk.get("level") else MISSING_OUTLOOK_RU,
        },
        "text_ru": None,
    }


def _fmt_dates(days: list[str]) -> str:
    if not days:
        return ""
    parsed: list[datetime] = []
    for d in days:
        try:
            parsed.append(datetime.fromisoformat(str(d)[:10]))
        except Exception:
            continue
    if not parsed:
        return ", ".join(days)
    months = "января февраля марта апреля мая июня июля августа сентября октября ноября декабря".split()
    return ", ".join(f"{p.day} {months[p.month - 1]}" for p in parsed)


def _window_ru(days: list[str]) -> str | None:
    if len(days) < 2:
        return _fmt_dates(days) or None
    try:
        a = datetime.fromisoformat(str(days[0])[:10])
        b = datetime.fromisoformat(str(days[-1])[:10])
    except Exception:
        return _fmt_dates(days)
    months = "января февраля марта апреля мая июня июля августа сентября октября ноября декабря".split()
    return f"{a.day}–{b.day} {months[b.month - 1]}"


def recommendations_from_forecast(
    forecast: list[dict[str, Any]],
    *,
    tmax_avg: float | None,
    precip_7: float | None,
    humidity: float | None,
    wind: float | None,
    crop_id: str | None,
) -> list[dict[str, Any]]:
    general = crop_id is None
    days = [d for d in forecast if d.get("date")]
    dry = [d for d in days if (d.get("precip") is None or float(d.get("precip") or 0) < 2) and (d.get("precip_probability") is None or float(d.get("precip_probability") or 0) < 40)]
    calm = [d for d in dry if d.get("wind") is None or float(d.get("wind") or 0) < 5]
    windy = [d for d in days if d.get("wind") is not None and float(d["wind"]) >= 5]
    wet = [d for d in days if (d.get("precip") is not None and float(d["precip"]) >= 4) or (d.get("precip_probability") is not None and float(d["precip_probability"]) >= 55)]
    hot = bool(tmax_avg is not None and tmax_avg >= 30)
    dry_week = bool(precip_7 is not None and precip_7 < 8)
    wet_week = bool(precip_7 is not None and precip_7 >= 28)
    dry_dates = [str(d["date"])[:10] for d in dry[:5]]
    calm_dates = [str(d["date"])[:10] for d in calm[:5]]
    wet_dates = [str(d["date"])[:10] for d in wet[:5]]

    def pack(kind: dict[str, str], status: str, status_ru: str, reason: str, dates: list[str] | None = None, window: str | None = None) -> dict[str, Any]:
        return {
            "id": kind["id"],
            "category_ru": kind["category_ru"],
            "icon": kind["icon"],
            "status": status,
            "status_ru": status_ru,
            "reason_ru": reason,
            "dates": dates or [],
            "window_ru": window,
            "general": general,
            "crop_id": crop_id,
            "crop_ru": crop_label_ru(crop_id),
            "context_ru": GENERAL_INDICATOR_RU if general else CROP_CONTEXT_RU,
        }

    kinds = {k["id"]: k for k in WORK_KINDS}
    out: list[dict[str, Any]] = []

    if wet_week:
        out.append(pack(kinds["harvest"], "caution", "С осторожностью", "Высокая сумма осадков — риск полегания и сложности уборки.", wet_dates))
    elif dry_dates:
        out.append(pack(kinds["harvest"], "favorable", "Благоприятно", "Сухие дни на горизонте 7 дней.", dry_dates, _window_ru(dry_dates) or None))
    else:
        out.append(pack(kinds["harvest"], "insufficient", "Недостаточно данных", "Нет устойчивого окна по осадкам."))

    if calm_dates:
        out.append(pack(kinds["machinery"], "favorable", "Благоприятно", "Дни без существенных осадков.", calm_dates, _fmt_dates(calm_dates)))
    elif wet_week:
        out.append(pack(kinds["machinery"], "not_recommended", "Не рекомендуется", "Ожидаются осадки — вывоз техники лучше отложить.", wet_dates))
    else:
        out.append(pack(kinds["machinery"], "caution", "С осторожностью", "Окно по осадкам неоднозначное."))

    if wind is not None and wind >= 5:
        out.append(pack(kinds["spraying"], "not_recommended", "Не рекомендуется", "Сильный ветер — снос рабочего раствора."))
    elif wet:
        out.append(pack(kinds["spraying"], "not_recommended", "Не рекомендуется", "Ожидаются осадки.", wet_dates))
    elif wind is None and not days:
        out.append(pack(kinds["spraying"], "insufficient", "Недостаточно данных", "Нет данных по ветру и осадкам для опрыскивания."))
    else:
        out.append(pack(kinds["spraying"], "favorable", "Благоприятно", "По доступному прогнозу ветер и осадки не блокируют обработку.", calm_dates))

    if wet_week:
        out.append(pack(kinds["fertilizer"], "caution", "С осторожностью", "Избыток влаги — риск вымывания.", wet_dates))
    elif dry_week and hot:
        out.append(pack(kinds["fertilizer"], "caution", "С осторожностью", "Сухо и жарко — эффективность корневого внесения снижается."))
    else:
        out.append(pack(kinds["fertilizer"], "favorable" if dry_dates else "insufficient", "Благоприятно" if dry_dates else "Недостаточно данных", "По доступному ряду нет явного запрета." if dry_dates else "Нет окна по осадкам."))

    if dry_week and (humidity is None or humidity < 45):
        reason = "Низкая влажность и мало осадков." if humidity is not None else "Мало осадков на 7 дней."
        if crop_id in {"corn", "sunflower", "soy"}:
            reason += " Теплолюбивые культуры чувствительны к дефициту влаги."
        out.append(pack(kinds["irrigation"], "recommended", "Рекомендуется", reason))
    elif precip_7 is None:
        out.append(pack(kinds["irrigation"], "insufficient", "Недостаточно данных", "Нет суммы осадков для решения по поливу."))
    else:
        out.append(pack(kinds["irrigation"], "not_needed", "Не требуется", "Осадки на горизонте не указывают на срочный полив."))

    if dry_week and hot:
        reason = "Дефицит влаги."
        if crop_id in {"wheat", "barley", "rapeseed"}:
            reason = "Дефицит влаги для озимых/яровых зерновых."
        out.append(pack(kinds["sowing"], "high_risk", "Высокий риск", reason))
    elif wet_week:
        out.append(pack(kinds["sowing"], "caution", "С осторожностью", "Переувлажнение затрудняет посев."))
    elif precip_7 is None:
        out.append(pack(kinds["sowing"], "insufficient", "Недостаточно данных", "Нет данных по влаге для посева."))
    else:
        out.append(pack(kinds["sowing"], "favorable", "Благоприятно", "По доступному ряду нет критического дефицита или избытка влаги."))

    if wet_week:
        out.append(pack(kinds["tillage"], "not_recommended", "Не рекомендуется", "Переувлажнение почвы по осадкам — риск уплотнения."))
    elif dry_dates:
        out.append(pack(kinds["tillage"], "favorable", "Благоприятно", "Сухие дни подходят для обработки.", dry_dates, _window_ru(dry_dates)))
    else:
        out.append(pack(kinds["tillage"], "insufficient", "Недостаточно данных", "Нет устойчивого окна."))

    if wet_week or (humidity is not None and humidity >= 80):
        out.append(pack(kinds["plant_protection"], "caution", "Контроль", "Влажные условия повышают риск болезней — усилить мониторинг."))
    elif windy:
        out.append(pack(kinds["plant_protection"], "caution", "С осторожностью", "Ветер ограничивает контактные обработки."))
    else:
        out.append(pack(kinds["plant_protection"], "favorable", "По условиям", "По доступному ряду нет явного вспышечного сигнала."))
    return out


def calendar_from_recommendations(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    wanted = {"harvest", "machinery", "spraying", "fertilizer", "sowing", "irrigation"}
    out = []
    for rec in items:
        if rec.get("id") not in wanted:
            continue
        out.append(
            {
                "id": rec["id"],
                "title_ru": rec["category_ru"],
                "status_ru": rec["status_ru"],
                "status": rec["status"],
                "window_ru": rec.get("window_ru") or (_fmt_dates(rec.get("dates") or []) or None),
                "risk": rec.get("status"),
                "reason_ru": rec.get("reason_ru"),
            }
        )
    return out


def region_card(macro_id: str, members: list[dict[str, Any]]) -> dict[str, Any]:
    meta = macro_meta(macro_id)

    def avg(key: str) -> float | None:
        vals = [m.get(key) for m in members if m.get(key) is not None]
        if not vals:
            return None
        return round(sum(float(v) for v in vals) / len(vals), 1)

    tmax = avg("tmax_avg") if avg("tmax_avg") is not None else avg("temperature")
    precip_7 = None
    rains = [m.get("precip_7") for m in members if m.get("precip_7") is not None]
    if rains:
        precip_7 = round(sum(float(v) for v in rains) / len(rains), 1)
    humidity = avg("humidity")
    wind = avg("wind_speed")
    risk = agro_risk_from_metrics(tmax=tmax, precip_7=precip_7, humidity=humidity, wind=wind, tmin=avg("tmin"))
    if tmax is not None and tmax >= 30 and (precip_7 is not None and precip_7 < 10):
        feel = "Жарко / сухо"
    elif precip_7 is not None and precip_7 >= 28:
        feel = "Влажно"
    elif tmax is None:
        feel = "Нет данных"
    else:
        feel = "Умеренно"
    return {
        "id": macro_id,
        "title_ru": meta["title_full_ru"],
        "title_uk": meta["title_uk"],
        "short_ru": meta["title_card_ru"],
        "temperature": tmax,
        "feel_ru": feel,
        "precip_7": precip_7,
        "humidity": humidity,
        "wind_speed": wind,
        "agro_risk": risk,
        "missing": all(m.get("missing") for m in members) if members else True,
    }


def format_last_updated(ts: datetime | None) -> dict[str, Any]:
    if ts is None:
        return {"iso": None, "display_ru": None, "hours": None}
    local = ts.astimezone(timezone.utc)
    hours = (datetime.now(timezone.utc) - local).total_seconds() / 3600
    if hours < 0:
        hours = 0.0
    return {
        "iso": local.isoformat(),
        "display_ru": local.strftime("%d.%m.%Y %H:%M"),
        "hours": round(hours, 1),
    }
