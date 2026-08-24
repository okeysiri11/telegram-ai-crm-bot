"""AGRO 2.0 — business-language presentation. Technical details stay in diagnostics."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from services.agro_ops.analytics import is_numeric_observation
from services.agro_ops.engines import build_opportunities, build_risks

TECH_RE = re.compile(
    r"(HTTP\s+\d{3}|JSON\s+404|timeout|metadata_only|pipeline_version|METADATA_ONLY|probe_result)",
    re.I,
)

BUSINESS_REPORT_SECTIONS = [
    ("minute", "Главное за 1 минуту"),
    ("ukraine", "Украина"),
    ("world", "Мир"),
    ("weather_harvest", "Погода и урожай"),
    ("prices", "Цены"),
    ("trade", "Экспорт / импорт"),
    ("logistics", "Логистика"),
    ("risks", "Риски"),
    ("opportunities", "Возможности"),
    ("watch", "Что контролировать сегодня"),
]

SCHEDULE_PRESENTATION = [
    {"id": "ops_refresh", "time_kyiv": "05:45", "label_ru": "Обновление данных"},
    {"id": "morning_report", "time_kyiv": "06:00", "label_ru": "Утренний обзор"},
    {"id": "light_refresh", "time_kyiv": "12:00", "label_ru": "Промежуточное обновление"},
    {"id": "full_refresh", "time_kyiv": "17:30", "label_ru": "Полное обновление"},
    {"id": "evening_report", "time_kyiv": "18:00", "label_ru": "Вечерний обзор"},
    {"id": "weekly_report", "time_kyiv": "09:00", "weekday_ru": "воскресенье", "label_ru": "Недельный прогноз"},
    {"id": "monthly_outlook", "time_kyiv": "08:00", "day_ru": "1-е число", "label_ru": "Прогноз 1–2 месяца"},
]


def is_technical_text(text: str) -> bool:
    return bool(TECH_RE.search(text or ""))


def cron_to_human(cron_kyiv: str) -> dict[str, str]:
    parts = str(cron_kyiv or "").split()
    if len(parts) < 5:
        return {"time_kyiv": "", "when_ru": ""}
    minute, hour, dom, _month, dow = parts[:5]
    time_kyiv = f"{int(hour):02d}:{int(minute):02d}" if hour.isdigit() and minute.isdigit() else cron_kyiv
    if dow not in {"*", "?"} and dow.isdigit():
        names = {"0": "воскресенье", "1": "понедельник", "2": "вторник", "3": "среда", "4": "четверг", "5": "пятница", "6": "суббота"}
        return {"time_kyiv": time_kyiv, "when_ru": names.get(dow, ""), "cron_kyiv": cron_kyiv}
    if dom not in {"*", "?"}:
        return {"time_kyiv": time_kyiv, "when_ru": "1-е число" if dom == "1" else f"день {dom}", "cron_kyiv": cron_kyiv}
    return {"time_kyiv": time_kyiv, "when_ru": "ежедневно", "cron_kyiv": cron_kyiv}


def present_schedule(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    by_id = {str(j.get("id")): j for j in jobs}
    for spec in SCHEDULE_PRESENTATION:
        job = by_id.get(spec["id"]) or {}
        human = cron_to_human(str(job.get("cron_kyiv") or ""))
        out.append(
            {
                **spec,
                **job,
                "time_kyiv": human.get("time_kyiv") or spec["time_kyiv"],
                "when_ru": human.get("when_ru") or spec.get("weekday_ru") or spec.get("day_ru") or "ежедневно",
                "cron_kyiv": job.get("cron_kyiv"),
            }
        )
    return out


def business_brief(providers: list[dict[str, Any]], observations: list[dict[str, Any]]) -> dict[str, Any]:
    connected = [
        p
        for p in providers
        if str(p.get("health_state") or "") in {"CONNECTED", "PARTIAL", "DEGRADED", "STALE"}
        and str(p.get("id") or "") != "manual_import"
    ]
    kinds = {str(o.get("series_kind") or "") for o in observations if is_numeric_observation(o)}
    parts = []
    if "weather" in kinds:
        parts.append("погоде")
    if "fx" in kinds:
        parts.append("валюте")
    if "trade" in kinds:
        parts.append("торговле")
    if "price" in kinds:
        parts.append("рынкам")
    if not parts:
        text = "Свежих рыночных рядов пока нет. Источники можно проверить в настройках."
    else:
        text = "Получены свежие данные по " + ", ".join(parts[:-1] + ([" и ".join(parts[-1:])] if parts else [])) + "."
        if len(parts) == 1:
            text = f"Получены свежие данные по {parts[0]}."
        elif len(parts) == 2:
            text = f"Получены свежие данные по {parts[0]} и {parts[1]}."
        else:
            text = "Получены свежие данные по " + ", ".join(parts[:-1]) + f" и {parts[-1]}."
    return {
        "text_ru": text,
        "connected_n": len(connected),
        "has_numeric": bool(kinds),
    }


def risk_cards(observations: list[dict[str, Any]], providers: list[dict[str, Any]], trips: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    engine = build_risks(observations, providers, lots=None, contracts=None)
    grouped: dict[str, dict[str, Any]] = {}
    mapping = {
        "weather": "Погода",
        "logistics": "Логистика",
        "price": "Цена",
        "trade": "Экспорт",
        "fx": "Валюта",
        "harvest": "Урожай",
        "production": "Урожай",
        "ports": "Логистика",
    }
    for row in engine:
        kind = str(row.get("kind") or row.get("code") or "other")
        label = mapping.get(kind)
        if not label:
            text = str(row.get("text") or "").lower()
            if "погод" in text:
                label = "Погода"
            elif "логист" in text or "фрахт" in text or "порт" in text:
                label = "Логистика"
            elif "курс" in text or "fx" in text or "валют" in text:
                label = "Валюта"
            elif "экспорт" in text or "торг" in text:
                label = "Экспорт"
            elif "урожа" in text:
                label = "Урожай"
            elif "цен" in text:
                label = "Цена"
            else:
                continue
        prev = grouped.get(label)
        severity = str(row.get("level") or "MEDIUM")
        if prev is None or _sev_rank(severity) < _sev_rank(str(prev.get("severity"))):
            grouped[label] = {
                "id": label.lower(),
                "title_ru": label,
                "severity": severity,
                "summary_ru": row.get("text"),
                "why_ru": row.get("reason") or row.get("text"),
                "monitor_ru": "Следить за официальными обновлениями и внутренними операциями.",
            }
    order = ["Погода", "Логистика", "Цена", "Экспорт", "Валюта", "Урожай"]
    return [grouped[k] for k in order if k in grouped]


def opportunity_cards(observations: list[dict[str, Any]], trips: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    rows = build_opportunities(observations, trips or [])
    out = []
    for row in rows[:6]:
        out.append(
            {
                "label_ru": row.get("label_ru") or "Потенциальная возможность",
                "region": row.get("buy_market") or row.get("sell_market"),
                "commodity": row.get("commodity"),
                "reason_ru": row.get("text"),
                "signal_ru": (
                    f"Спред {row.get('price_difference')} {row.get('currency') or ''}"
                    if row.get("price_difference") is not None
                    else "Недостаточно совместимых рядов"
                ),
                "confidence": row.get("data_confidence"),
                "guaranteed_profit": False,
            }
        )
    return out


def what_changed_24h(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)
    by_series: dict[str, list[dict[str, Any]]] = {}
    for obs in observations:
        if not is_numeric_observation(obs):
            continue
        key = str(obs.get("series_id") or f"{obs.get('provider_id')}:{obs.get('series_kind')}:{obs.get('unit')}")
        by_series.setdefault(key, []).append(obs)
    out: list[dict[str, Any]] = []
    for key, rows in by_series.items():
        rows = sorted(rows, key=lambda r: str(r.get("observed_at") or r.get("published_at") or ""))
        if len(rows) < 2:
            continue
        last = rows[-1]
        prev = rows[-2]
        last_ts = last.get("observed_at") or last.get("published_at")
        try:
            ts = datetime.fromisoformat(str(last_ts).replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts < cutoff:
                continue
        except Exception:
            continue
        try:
            a = float(prev.get("normalized_value"))
            b = float(last.get("normalized_value"))
        except (TypeError, ValueError):
            continue
        if not a:
            continue
        pct = round((b - a) / abs(a) * 100, 1)
        if abs(pct) < 0.2:
            continue
        kind = str(last.get("series_kind") or "")
        sign = "+" if pct > 0 else ""
        unit = last.get("unit") or ""
        if kind == "price":
            text = f"Цена {last.get('commodity') or last.get('title')}: {sign}{pct}%"
        elif kind == "fx":
            text = f"{last.get('commodity') or 'валюта'}: {sign}{pct}%"
        elif kind == "weather" and unit == "mm":
            delta = round(b - a, 1)
            text = f"Осадки {last.get('region') or ''}: {delta:+} mm".strip()
        elif kind == "weather":
            text = f"Температура {last.get('region') or ''}: {sign}{pct}%".strip()
        elif kind == "trade":
            text = f"Торговля {last.get('commodity') or ''}: {sign}{pct}%".strip()
        else:
            text = f"{last.get('title') or key}: {sign}{pct}%"
        out.append(
            {
                "series_kind": kind,
                "text_ru": text,
                "pct": pct,
                "provider_id": last.get("provider_id"),
            }
        )
    return out[:12]


def business_report_sections(sections: list[dict[str, Any]] | dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(sections, dict):
        items = [{"id": k, **(v if isinstance(v, dict) else {"text": v})} for k, v in sections.items()]
    else:
        items = list(sections or [])
    by_id = {str(s.get("id")): s for s in items}
    mapped = {
        "minute": by_id.get("chief") or by_id.get("today") or by_id.get("minute"),
        "ukraine": by_id.get("ukraine"),
        "world": by_id.get("world"),
        "weather_harvest": by_id.get("weather") or by_id.get("harvest"),
        "prices": by_id.get("prices"),
        "trade": by_id.get("trade"),
        "logistics": by_id.get("logistics"),
        "risks": by_id.get("risks"),
        "opportunities": by_id.get("opportunities"),
        "watch": by_id.get("today") or by_id.get("watch"),
    }
    out = []
    for sid, label in BUSINESS_REPORT_SECTIONS:
        src = mapped.get(sid) or {}
        bullets = src.get("bullets") or []
        compact = []
        for b in bullets[:3]:
            if isinstance(b, dict):
                compact.append({"text": b.get("text") or b.get("summary"), "detail": b})
            else:
                compact.append({"text": str(b)})
        out.append(
            {
                "id": sid,
                "label_ru": label,
                "compact": compact,
                "full": bullets,
                "note_ru": src.get("note_ru") or src.get("conclusion_ru"),
            }
        )
    return out


def strip_tech_from_provider(row: dict[str, Any]) -> dict[str, Any]:
    note = str(row.get("note_ru") or "")
    error = str(row.get("error") or "")
    business_note = note
    if is_technical_text(note):
        hs = str(row.get("health_state") or "")
        business_note = {
            "CONNECTED": "Источник отвечает, данные получены.",
            "PARTIAL": "Источник отвечает частично.",
            "METADATA_ONLY": "Источник открывается, но без числового ряда.",
            "NEEDS_KEY": "Нужен ключ доступа.",
            "NEEDS_LICENSE": "Нужна лицензия.",
            "BLOCKED": "Источник сейчас недоступен.",
            "FAILED": "Источник сейчас недоступен.",
            "OPTIONAL_NOT_CONFIGURED": "Дополнительный источник не настроен.",
        }.get(hs, "Состояние источника смотрите в диагностике.")
    return {
        **row,
        "business_note_ru": business_note,
        "error_hidden": bool(error) or is_technical_text(note),
    }


def _sev_rank(level: str) -> int:
    return {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(str(level).upper(), 9)
