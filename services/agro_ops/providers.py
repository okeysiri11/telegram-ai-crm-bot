"""AGRO 1.6 — official-source adapters with numeric series.

CONNECTED only after a real HTTP retrieval yields finite `normalized_value`.
HTTP 200 + catalog titles / HTML headings = PARTIAL metadata, not market data.
Nothing is fabricated.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Protocol
from services.agro_ops.rbac import require

FetchFn = Callable[[str, dict[str, str] | None], Awaitable["FetchResult"]]

CONNECTION_STATUSES = (
    "CONNECTED",
    "DEGRADED",
    "STALE",
    "NOT_CONFIGURED",
    "UNAVAILABLE",
    "ERROR",
)

PROBE_RESULTS = ("CONNECTED", "PARTIAL", "NOT_CONFIGURED", "BLOCKED", "UNAVAILABLE", "FAILED", "NEEDS_KEY")
HEALTH_STATES = (
    "CONNECTED",
    "PARTIAL",
    "METADATA_ONLY",
    "STALE",
    "BLOCKED",
    "NEEDS_KEY",
    "NEEDS_LICENSE",
    "OPTIONAL_NOT_CONFIGURED",
    "FAILED",
)
HEALTH_COLORS = {
    "CONNECTED": "green",
    "PARTIAL": "yellow",
    "STALE": "yellow",
    "NEEDS_KEY": "orange",
    "NEEDS_LICENSE": "orange",
    "BLOCKED": "red",
    "FAILED": "red",
    "METADATA_ONLY": "gray",
    "OPTIONAL_NOT_CONFIGURED": "gray",
    "REQUIRES_CONFIGURATION": "gray",
    "NOT_CONFIGURED": "gray",
}

# Suggested Europe/Kyiv slots (cron stored as UTC in DEFAULT_JOBS).
DEFAULT_AGRO_SCHEDULE: dict[str, Any] = {
    "timezone": "Europe/Kyiv",
    "jobs": [
        {
            "id": "ops_refresh",
            "label_ru": "Обновление погоды / FX / операционка",
            "cron_kyiv": "45 5 * * *",
            "job_key": "agro.providers.dawn",
        },
        {
            "id": "morning_report",
            "label_ru": "Утренний анализ",
            "cron_kyiv": "0 6 * * *",
            "job_key": "agro.analysis.morning",
        },
        {
            "id": "light_refresh",
            "label_ru": "Лёгкое обновление",
            "cron_kyiv": "0 12 * * *",
            "job_key": "agro.providers.noon",
        },
        {
            "id": "full_refresh",
            "label_ru": "Полное обновление источников",
            "cron_kyiv": "30 17 * * *",
            "job_key": "agro.providers.full",
        },
        {
            "id": "evening_report",
            "label_ru": "Вечерний анализ",
            "cron_kyiv": "0 18 * * *",
            "job_key": "agro.analysis.evening",
        },
        {
            "id": "weekly_report",
            "label_ru": "Недельный обзор (воскресенье)",
            "cron_kyiv": "0 9 * * 0",
            "job_key": "agro.analysis.weekly",
        },
        {
            "id": "monthly_outlook",
            "label_ru": "Прогноз 1–2 месяца (1-е число)",
            "cron_kyiv": "0 8 1 * *",
            "job_key": "agro.analysis.outlook",
        },
    ],
}

NOT_CONFIGURED_RU = "Требуется подключение источника"
NOT_SETUP_RU = "Требуется настройка"
UNAVAILABLE_RU = "Источник недоступен"
BLOCKED_RU = "Доступ к источнику запрещён"
PARTIAL_RU = "Официальная страница доступна, структурированные данные не разобраны"

NEEDS_KEY_RU = "Нужен API-ключ"
USER_AGENT = "ADOS-AgroOps/1.6 (+https://ados.local; official-open-data probe)"
TIMEOUT_SEC = 18


class FetchResult(Protocol):
    status: int
    text: str
    headers: dict[str, str]
    error: str | None
    blocked: bool
    unavailable: bool


class SimpleFetchResult:
    def __init__(
        self,
        status: int = 0,
        text: str = "",
        headers: dict[str, str] | None = None,
        error: str | None = None,
        blocked: bool = False,
        unavailable: bool = False,
        timed_out: bool = False,
        rate_limited: bool = False,
        content_type: str = "",
        truncated: bool = False,
    ) -> None:
        self.status = status
        self.text = text
        self.headers = headers or {}
        self.error = error
        self.blocked = blocked
        self.unavailable = unavailable
        self.timed_out = timed_out
        self.rate_limited = rate_limited or status == 429
        self.content_type = content_type or str((headers or {}).get("Content-Type") or (headers or {}).get("content-type") or "")
        self.truncated = truncated


PROVIDER_SPECS: list[dict[str, Any]] = [
    {
        "id": "ua_customs_open_data",
        "label_ru": "Таможня Украины / открытые данные",
        "category": "trade",
        "country": "UA",
        "region": "Украина",
        "source_type": "open_data_api",
        "official": True,
        "priority": 1,
        "url": "https://data.gov.ua/api/3/action/package_search?q=%D0%BC%D0%B8%D1%82%D0%BD%D0%B8%D1%86%D1%8F&rows=12",
        "license_note_ru": "Открытые данные data.gov.ua / Гостаможслужба. Только опубликованные наборы.",
        "receives_ru": "Экспорт/импорт, товарные группы, страны-партнёры — если набор опубликован в CKAN",
        "cadence": "daily",
        "observation_kind": "trade_observation",
    },
    {
        "id": "ua_stat",
        "label_ru": "Госстат Украины",
        "category": "statistics",
        "country": "UA",
        "region": "Украина",
        "source_type": "open_data_api",
        "official": True,
        "priority": 1,
        "url": "https://data.gov.ua/api/3/action/package_search?q=%D1%81%D1%96%D0%BB%D1%8C%D1%81%D1%8C%D0%BA%D0%B5+%D0%B3%D0%BE%D1%81%D0%BF%D0%BE%D0%B4%D0%B0%D1%80%D1%81%D1%82%D0%B2%D0%BE&rows=12",
        "license_note_ru": "Открытые наборы Госстата на data.gov.ua. Без скрапинга закрытых кабинетов.",
        "receives_ru": "Посевные площади, производство, урожайность, запасы, средние цены — если набор открыт",
        "cadence": "daily",
        "observation_kind": "crop_observation",
    },
    {
        "id": "ua_hydromet",
        "label_ru": "Укргидрометцентр",
        "category": "weather",
        "country": "UA",
        "region": "Украина",
        "source_type": "official_page",
        "official": True,
        "priority": 1,
        "url": "https://meteo.gov.ua/",
        "license_note_ru": "Официальный сайт Укргидрометцентра. Агрессивный скрапинг запрещён.",
        "receives_ru": "Агрометеосводки, осадки, предупреждения — только с официальной страницы",
        "cadence": "several_per_day",
        "observation_kind": "weather_observation",
    },
    {
        "id": "weather_provider_secondary",
        "label_ru": "Погодный провайдер (резерв)",
        "category": "weather",
        "country": "UA",
        "region": "Украина",
        "source_type": "licensed",
        "official": False,
        "priority": 2,
        "url": "",
        "license_note_ru": "Слот зарезервирован. Надёжный легальный провайдер ещё не выбран.",
        "receives_ru": "Резервная погода — не подключён",
        "cadence": "several_per_day",
        "observation_kind": "weather_observation",
        "fixed_status": "NOT_CONFIGURED",
        "needs_key": True,
    },
    {
        "id": "usda_wasde",
        "label_ru": "USDA / WASDE (минсельхоз США)",
        "category": "world_balance",
        "country": "US",
        "region": "Мир",
        "source_type": "official_api",
        "official": True,
        "priority": 1,
        "url": "https://usda.library.cornell.edu/concern/publications/3t945q76s.json",
        "fallback_urls": [
            "https://esmis.nal.usda.gov/concern/publications/3t945q76s.json",
            "https://www.usda.gov/about-usda/general-information/staff-offices/office-chief-economist/commodity-markets/wasde-report",
        ],
        "needs_key_env": "USDA_FAS_API_KEY",
        "license_note_ru": "Публикации WASDE. Числовой FAS Open Data API требует ключ USDA_FAS_API_KEY.",
        "receives_ru": "Баланс пшеницы/кукурузы — только если JSON с числами доступен; иначе страница/каталог",
        "cadence": "daily_check_new_release",
        "observation_kind": "crop_observation",
    },
    {
        "id": "fao",
        "label_ru": "ФАО / FAOSTAT",
        "category": "prices",
        "country": "INTL",
        "region": "Мир",
        "source_type": "official_api",
        "official": True,
        "priority": 1,
        "parser": "faostat",
        "url": "https://fenixservices.fao.org/faostat/api/v1/en/data/QCL?area=230&item=15&element=5510&year=2022,2023,2024",
        "timeout_sec": 12,
        "retries": 0,
        "prefer_extra_urls": True,
        "extra_urls": [
            {
                "url": "https://www.fao.org/media/docs/worldfoodsituationlibraries/default-document-library/food_price_indices_data.csv?sfvrsn=523ebd2a_82&download=true",
                "series_id": "faostat-fpi-cereals",
            },
            {
                "url": "https://www.fao.org/fileadmin/templates/worldfood/Reports_and_docs/Food_price_indices_data.csv",
                "series_id": "faostat-fpi-cereals",
            },
        ],
        "fallback_urls": [],
        "license_note_ru": "FAOSTAT / официальный FAO Food Price Index. Лицензия FAO на открытые статистические данные.",
        "receives_ru": "FAO Food Price Index (Cereals). QCL-тонны — только если fenix API отвечает числами",
        "cadence": "weekly",
        "observation_kind": "crop_observation",
    },
    {
        "id": "ec_agri",
        "label_ru": "Еврокомиссия — рынок зерновых",
        "category": "eu_market",
        "country": "EU",
        "region": "ЕС",
        "source_type": "official_api",
        "official": True,
        "priority": 1,
        "parser": "ec_cereal",
        "url": "https://www.ec.europa.eu/agrifood/api/cereal/prices?beginDate={beginDate}&endDate={endDate}&memberStateCodes=FR",
        "license_note_ru": "EC Agri-food cereal prices API (официальный JSON).",
        "receives_ru": "Недельные цены зерновых ЕС в EUR/т",
        "cadence": "weekly",
        "observation_kind": "price_observation",
    },
    {
        "id": "eurostat",
        "label_ru": "Евростат",
        "category": "eu_market",
        "country": "EU",
        "region": "ЕС",
        "source_type": "official_api",
        "official": True,
        "priority": 2,
        "parser": "eurostat_sdmx",
        "url": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tag00047?format=JSON&lang=EN",
        "license_note_ru": "Eurostat dissemination API, открытая статистика ЕС (SDMX JSON).",
        "receives_ru": "Пшеница ЕС: площадь / производство / урожайность (tag00047)",
        "cadence": "weekly",
        "observation_kind": "crop_observation",
    },
    {
        "id": "ua_agro_ministry",
        "label_ru": "Минагрополитики Украины",
        "category": "official",
        "country": "UA",
        "region": "Украина",
        "source_type": "official_page",
        "official": True,
        "priority": 2,
        "url": "https://minagro.gov.ua/",
        "license_note_ru": "Официальный сайт министерства. Без закрытых кабинетов.",
        "receives_ru": "Официальные сообщения и опубликованные материалы",
        "cadence": "daily",
        "observation_kind": "market_observation",
    },
    {
        "id": "ua_ports",
        "label_ru": "Порты / инфраструктура",
        "category": "logistics",
        "country": "UA",
        "region": "Украина",
        "source_type": "official_page",
        "official": True,
        "priority": 3,
        "url": "https://www.uspa.gov.ua/",
        "license_note_ru": "Администрация морских портов Украины, открытые страницы.",
        "receives_ru": "Инфраструктура портов — если страница доступна",
        "cadence": "daily",
        "observation_kind": "trade_observation",
    },
    {
        "id": "amis",
        "label_ru": "AMIS (информация о рынках с/х)",
        "category": "outlook",
        "country": "INTL",
        "region": "Мир",
        "source_type": "official_page",
        "official": True,
        "priority": 3,
        "url": "https://www.amis-outlook.org/",
        "license_note_ru": "AMIS Outlook, открытый портал.",
        "receives_ru": "Обзоры мировых рынков — если портал доступен",
        "cadence": "weekly",
        "observation_kind": "market_observation",
    },
    {
        "id": "world_bank",
        "label_ru": "Всемирный банк",
        "category": "outlook",
        "country": "UA",
        "region": "Украина",
        "source_type": "official_api",
        "official": True,
        "priority": 1,
        "parser": "worldbank",
        "url": "https://api.worldbank.org/v2/country/UKR/indicator/AG.PRD.CREL.MT?format=json&per_page=12",
        "extra_urls": [
            {"url": "https://api.worldbank.org/v2/country/UKR/indicator/AG.YLD.CREL.KG?format=json&per_page=12", "series_id": "wb-yield"},
            {"url": "https://api.worldbank.org/v2/country/UKR/indicator/AG.LND.CREL.HA?format=json&per_page=12", "series_id": "wb-area"},
            {"url": "https://api.worldbank.org/v2/country/UKR/indicator/TX.VAL.MRCH.CD.WT?format=json&per_page=12", "series_id": "wb-trade"},
            {"url": "https://api.worldbank.org/v2/country/UKR/indicator/TM.VAL.MRCH.CD.WT?format=json&per_page=12", "series_id": "wb-import"},
        ],
        "timeout_sec": 25,
        "license_note_ru": "World Bank Open Data API (WDI). Официальные годовые ряды Украины.",
        "receives_ru": "Производство/урожайность/площадь зерновых Украины и товарный экспорт",
        "cadence": "weekly",
        "observation_kind": "crop_observation",
    },
    {
        "id": "market_prices",
        "label_ru": "Рыночные цены (лицензируемый провайдер)",
        "category": "prices",
        "country": "INTL",
        "region": "Мир",
        "source_type": "licensed",
        "official": False,
        "priority": 2,
        "url": "",
        "needs_key": True,
        "license_note_ru": "Коммерческий фид котировок. Ключ не задан.",
        "receives_ru": "Биржевые/спот котировки — требуется лицензия",
        "cadence": "morning_evening",
        "observation_kind": "price_observation",
        "fixed_status": "NEEDS_KEY",
    },
    {
        "id": "fx_rates",
        "label_ru": "НБУ — официальный курс",
        "category": "fx",
        "country": "UA",
        "region": "Украина",
        "source_type": "official_api",
        "official": True,
        "priority": 1,
        "parser": "nbu_fx",
        "url": "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json",
        "license_note_ru": "Официальный API НБУ (тот же URL, что market_reference_connectors). USD и EUR к гривне.",
        "receives_ru": "Курс USD/UAH и EUR/UAH",
        "cadence": "morning_evening",
        "observation_kind": "price_observation",
    },
    {
        "id": "weather_provider",
        "label_ru": "Open-Meteo (Киев)",
        "category": "weather",
        "country": "UA",
        "region": "Киев",
        "source_type": "open_data_api",
        "official": True,
        "priority": 1,
        "parser": "open_meteo",
        "url": "https://api.open-meteo.com/v1/forecast?latitude=50.45&longitude=30.52&daily=temperature_2m_max,precipitation_sum&forecast_days=7&timezone=Europe%2FKyiv",
        "license_note_ru": "Open-Meteo Forecast API, CC BY. Не замена официальным сводкам Укргидрометцентра.",
        "receives_ru": "Суточный максимум температуры и сумма осадков, Киев",
        "cadence": "several_per_day",
        "observation_kind": "weather_observation",
    },
    {
        "id": "manual_import",
        "label_ru": "Ручной импорт / RSS",
        "category": "manual",
        "country": "ORG",
        "region": "Организация",
        "source_type": "manual",
        "official": False,
        "priority": 1,
        "url": "",
        "license_note_ru": "Данные вводит оператор. Дубликаты отсекаются.",
        "receives_ru": "Ручные сообщения и импорт",
        "cadence": "on_demand",
        "observation_kind": "market_observation",
        "fixed_status": "CONNECTED",
    },
]

PROVIDER_CATALOG = [
    {
        "id": p["id"],
        "label_ru": p["label_ru"],
        "group": {
            "trade": "УКРАИНА (официальные)",
            "statistics": "УКРАИНА (официальные)",
            "weather": "ПОГОДА",
            "official": "УКРАИНА (официальные)",
            "logistics": "УКРАИНА (официальные)",
            "world_balance": "МЕЖДУНАРОДНЫЕ",
            "prices": "РЫНОК",
            "eu_market": "МЕЖДУНАРОДНЫЕ",
            "outlook": "МЕЖДУНАРОДНЫЕ",
            "fx": "РЫНОК",
            "manual": "РУЧНОЙ ВВОД",
        }.get(p["category"], "ДРУГОЕ"),
        "kind": p["category"],
    }
    for p in PROVIDER_SPECS
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _spec(provider_id: str) -> dict[str, Any] | None:
    return next((p for p in PROVIDER_SPECS if p["id"] == provider_id), None)


def fingerprint(*parts: Any) -> str:
    raw = "|".join(str(p or "") for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def resolve_spec_url(spec: dict[str, Any], url: str | None = None) -> str:
    raw = url if url is not None else str(spec.get("url") or "")
    if "{beginDate}" in raw or "{endDate}" in raw:
        end = datetime.now(timezone.utc)
        begin = end - timedelta(days=70)
        raw = raw.replace("{beginDate}", begin.strftime("%d/%m/%Y")).replace("{endDate}", end.strftime("%d/%m/%Y"))
    return raw


def observation_is_numeric(obs: dict[str, Any]) -> bool:
    value = obs.get("normalized_value")
    if value in (None, "", "null"):
        return False
    try:
        return abs(float(value)) >= 0 or float(value) == 0.0
    except (TypeError, ValueError):
        return False


async def default_fetch(url: str, headers: dict[str, str] | None = None, **kwargs: Any) -> SimpleFetchResult:
    from services.agro_ops.http_safety import fetch_official

    return await fetch_official(
        url,
        headers,
        timeout_sec=kwargs.get("timeout_sec"),
        retries=kwargs.get("retries"),
    )


def _parse_ckan_packages(text: str, provider_id: str, source_url: str) -> list[dict[str, Any]]:
    try:
        body = json.loads(text)
    except Exception:
        return []
    result = body.get("result") if isinstance(body, dict) else None
    packages = (result or {}).get("results") if isinstance(result, dict) else None
    if not isinstance(packages, list):
        return []
    out: list[dict[str, Any]] = []
    for pkg in packages[:12]:
        if not isinstance(pkg, dict):
            continue
        title = str(pkg.get("title") or pkg.get("name") or "").strip()
        if not title:
            continue
        out.append(
            {
                "provider_id": provider_id,
                "source_url": source_url,
                "source_reference": str(pkg.get("id") or pkg.get("name") or title),
                "published_at": str(pkg.get("metadata_modified") or pkg.get("metadata_created") or ""),
                "country": "UA",
                "commodity": "",
                "unit": "",
                "raw_value": title,
                "normalized_value": None,
                "confidence": "medium",
                "title": title,
                "notes": str(pkg.get("notes") or "")[:400],
            }
        )
    return out


def _parse_wasde_catalog(text: str, provider_id: str, source_url: str) -> list[dict[str, Any]]:
    try:
        body = json.loads(text)
    except Exception:
        return []
    date_created = str(body.get("date_created") or body.get("date_published") or "")
    title = str(body.get("title") or "WASDE")
    files = body.get("file_sets") or body.get("members") or []
    out = [
        {
            "provider_id": provider_id,
            "source_url": source_url,
            "source_reference": str(body.get("id") or "wasde"),
            "published_at": date_created,
            "report_date": date_created[:10],
            "country": "WORLD",
            "commodity": "",
            "raw_value": title,
            "normalized_value": None,
            "confidence": "high",
            "title": title,
        }
    ]
    if isinstance(files, list):
        for fs in files[:6]:
            if not isinstance(fs, dict):
                continue
            out.append(
                {
                    "provider_id": provider_id,
                    "source_url": str(fs.get("url") or source_url),
                    "source_reference": str(fs.get("id") or fs.get("title") or title),
                    "published_at": str(fs.get("date_uploaded") or date_created),
                    "report_date": str(fs.get("date_uploaded") or date_created)[:10],
                    "country": "WORLD",
                    "commodity": "",
                    "raw_value": str(fs.get("title") or title),
                    "normalized_value": None,
                    "confidence": "high",
                    "title": str(fs.get("title") or title),
                }
            )
    return out


def _parse_faostat_domains(text: str, provider_id: str, source_url: str) -> list[dict[str, Any]]:
    try:
        body = json.loads(text)
    except Exception:
        return []
    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, list):
        return []
    out: list[dict[str, Any]] = []
    for row in data[:20]:
        if not isinstance(row, dict):
            continue
        name = str(row.get("domain_name") or row.get("group_name") or row.get("label") or "").strip()
        if not name:
            continue
        out.append(
            {
                "provider_id": provider_id,
                "source_url": source_url,
                "source_reference": str(row.get("domain_code") or row.get("group_code") or name),
                "published_at": _now(),
                "country": "INTL",
                "commodity": "",
                "raw_value": name,
                "normalized_value": None,
                "confidence": "medium",
                "title": name,
            }
        )
    return out


def _parse_worldbank(text: str, provider_id: str, source_url: str) -> list[dict[str, Any]]:
    try:
        body = json.loads(text)
    except Exception:
        return []
    rows = body[1] if isinstance(body, list) and len(body) > 1 and isinstance(body[1], list) else []
    out: list[dict[str, Any]] = []
    for row in rows[:12]:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or row.get("id") or "").strip()
        if not name:
            continue
        out.append(
            {
                "provider_id": provider_id,
                "source_url": source_url,
                "source_reference": str(row.get("id") or name),
                "published_at": _now(),
                "country": "INTL",
                "raw_value": name,
                "normalized_value": None,
                "confidence": "medium",
                "title": name,
            }
        )
    return out


def classify_source_url(url: str) -> str:
    from urllib.parse import urlparse

    raw = (url or "").strip()
    host = (urlparse(raw).hostname or "").lower()
    path = (urlparse(raw).path or "").lower()
    query = (urlparse(raw).query or "").lower()
    if not host:
        return "UNKNOWN"
    if "rss" in path or "atom" in path or path.endswith(".xml") or "rss" in query:
        return "RSS"
    official_api = (
        "bank.gov.ua",
        "api.worldbank.org",
        "ec.europa.eu",
        "api.tech.ec.europa.eu",
        "api.open-meteo.com",
        "fenixservices.fao.org",
    )
    public_data = ("europa.eu", "fao.org", "worldbank.org", "data.gov.ua", "open-meteo.com", "usda.gov", "un.org")
    if any(host == h or host.endswith("." + h) for h in official_api):
        return "OFFICIAL_API"
    if any(host == h or host.endswith("." + h) for h in public_data):
        return "PUBLIC_DATA"
    return "UNKNOWN"


def health_state(connection_status: str, probe_result: str | None = None) -> str:
    probe = (probe_result or "").upper()
    status = (connection_status or "").upper()
    if probe == "BLOCKED" or status == "BLOCKED":
        return "BLOCKED"
    if status == "STALE" or probe == "STALE":
        return "STALE"
    if status == "NEEDS_KEY" or probe == "NEEDS_KEY":
        return "NEEDS_KEY"
    if status == "CONNECTED":
        return "CONNECTED"
    if status == "DEGRADED" or probe == "PARTIAL":
        return "PARTIAL"
    if status == "NOT_CONFIGURED":
        return "REQUIRES_CONFIGURATION"
    if probe == "FAILED" or status in {"ERROR", "UNAVAILABLE"}:
        return "FAILED"
    return "REQUIRES_CONFIGURATION"


def normalize_observation(obs: dict[str, Any], spec: dict[str, Any], ingested_at: str) -> dict[str, Any]:
    numeric = observation_is_numeric(obs)
    data_class = str(obs.get("data_class") or ("numeric" if numeric else "metadata"))
    if obs.get("is_demo") or data_class == "demo":
        data_class = "demo"
    return {
        **obs,
        "provider_id": obs.get("provider_id") or spec.get("id"),
        "source_url": obs.get("source_url") or spec.get("url"),
        "source_reference": obs.get("source_reference") or obs.get("title") or spec.get("id"),
        "adapter_type": spec.get("source_type"),
        "source_class": obs.get("source_class") or spec.get("source_class") or spec.get("source_type") or "",
        "trust_level": obs.get("trust_level") or spec.get("trust_level") or "",
        "observed_at": obs.get("observed_at") or ingested_at,
        "published_at": obs.get("published_at") or ingested_at,
        "ingested_at": ingested_at,
        "country": obs.get("country") or spec.get("country") or "",
        "region": obs.get("region") or spec.get("region") or "",
        "commodity": obs.get("commodity") or "",
        "unit": obs.get("unit") or "",
        "currency": obs.get("currency") or "",
        "raw_value": obs.get("raw_value"),
        "normalized_value": obs.get("normalized_value"),
        "value": obs.get("value") if obs.get("value") not in (None, "") else obs.get("normalized_value"),
        "confidence": obs.get("confidence") or "medium",
        "freshness": obs.get("freshness") or "LIVE",
        "canonical_type": obs.get("canonical_type") or KIND_CANONICAL.get(str(spec.get("observation_kind") or ""), "AgroIntelligenceItem"),
        "data_class": data_class,
        "market_usable": bool(obs.get("market_usable")) if "market_usable" in obs else numeric,
        "series_id": obs.get("series_id") or "",
        "series_kind": obs.get("series_kind") or "",
        "sections": list(obs.get("sections") or ()),
    }


def _html_reachable(text: str) -> bool:
    low = text.lower()
    return "<html" in low or "<!doctype" in low or "meteo" in low or "agridata" in low or "minagro" in low


def _strip_html(value: str) -> str:
    import re

    cleaned = re.sub(r"<script[\s\S]*?</script>", " ", value, flags=re.I)
    cleaned = re.sub(r"<style[\s\S]*?</style>", " ", cleaned, flags=re.I)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = cleaned.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
    return " ".join(cleaned.split())[:240]


def _parse_html_signals(text: str, provider_id: str, source_url: str) -> list[dict[str, Any]]:
    """Normalize page title/headings — never pass raw HTML to analysts."""
    import re

    out: list[dict[str, Any]] = []
    title_m = re.search(r"<title[^>]*>(.*?)</title>", text or "", flags=re.I | re.S)
    title = _strip_html(title_m.group(1)) if title_m else ""
    if title:
        out.append(
            {
                "provider_id": provider_id,
                "source_url": source_url,
                "source_reference": "html-title",
                "published_at": _now(),
                "raw_value": title,
                "normalized_value": None,
                "confidence": "low",
                "title": title,
                "canonical_type": "page_signal",
            }
        )
    for heading in re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", text or "", flags=re.I | re.S)[:8]:
        label = _strip_html(heading)
        if not label or len(label) < 4:
            continue
        if any(i.get("title") == label for i in out):
            continue
        out.append(
            {
                "provider_id": provider_id,
                "source_url": source_url,
                "source_reference": "html-heading",
                "published_at": _now(),
                "raw_value": label,
                "normalized_value": None,
                "confidence": "low",
                "title": label,
                "canonical_type": "page_signal",
            }
        )
    return out[:8]


KIND_CANONICAL = {
    "trade_observation": "AgroTradeObservation",
    "price_observation": "AgroPriceObservation",
    "weather_observation": "AgroWeatherObservation",
    "crop_observation": "AgroProductionObservation",
    "market_observation": "AgroGlobalMarketObservation",
}


def _parse_legacy_metadata(spec: dict[str, Any], text: str, url: str) -> list[dict[str, Any]]:
    pid = spec["id"]
    if pid in {"ua_customs_open_data", "ua_stat"}:
        rows = _parse_ckan_packages(text, pid, url)
        for row in rows:
            row["data_class"] = "metadata"
            row["market_usable"] = False
            row["canonical_type"] = "page_signal"
        return rows
    if pid == "usda_wasde":
        rows = _parse_wasde_catalog(text, pid, url)
        for row in rows:
            row["data_class"] = "metadata"
            row["market_usable"] = False
        return rows
    if pid == "fao":
        rows = _parse_faostat_domains(text, pid, url)
        for row in rows:
            row["data_class"] = "metadata"
            row["market_usable"] = False
        return rows
    return []


def interpret_fetch(spec: dict[str, Any], fetched: SimpleFetchResult, *, source_url: str | None = None) -> dict[str, Any]:
    import os

    if spec.get("fixed_status") in {"NOT_CONFIGURED", "NEEDS_KEY"} or (not spec.get("url") and spec.get("fixed_status")):
        needs_key = spec.get("fixed_status") == "NEEDS_KEY" or spec.get("needs_key") or spec.get("source_type") == "licensed"
        return {
            "connection_status": "NEEDS_KEY" if needs_key else "NOT_CONFIGURED",
            "probe_result": "NEEDS_KEY" if needs_key else "NOT_CONFIGURED",
            "freshness": "NOT_CONFIGURED",
            "error": "",
            "note_ru": NEEDS_KEY_RU if needs_key else (NOT_SETUP_RU if spec.get("source_type") == "licensed" else NOT_CONFIGURED_RU),
            "observations": [],
            "market_usable": False,
        }
    if spec.get("fixed_status") == "CONNECTED":
        return {
            "connection_status": "CONNECTED",
            "probe_result": "CONNECTED",
            "freshness": "LIVE",
            "error": "",
            "note_ru": "Доступен: данные вводятся вручную или импортируются",
            "observations": [],
            "market_usable": False,
        }
    key_env = str(spec.get("needs_key_env") or "")
    if key_env and not os.environ.get(key_env) and spec.get("require_key"):
        return {
            "connection_status": "NEEDS_KEY",
            "probe_result": "NEEDS_KEY",
            "freshness": "NOT_CONFIGURED",
            "error": f"missing {key_env}",
            "note_ru": f"{NEEDS_KEY_RU}: {key_env}",
            "observations": [],
            "market_usable": False,
        }
    if getattr(fetched, "timed_out", False):
        return {
            "connection_status": "ERROR",
            "probe_result": "FAILED",
            "freshness": "UNAVAILABLE",
            "error": fetched.error or "timeout",
            "note_ru": "Таймаут источника — числовой ряд не получен",
            "observations": [],
            "market_usable": False,
        }
    if getattr(fetched, "rate_limited", False) or fetched.status == 429:
        retry = (fetched.headers or {}).get("Retry-After") or (fetched.headers or {}).get("retry-after") or ""
        return {
            "connection_status": "ERROR",
            "probe_result": "FAILED",
            "freshness": "UNAVAILABLE",
            "error": f"HTTP 429{(' retry-after=' + retry) if retry else ''}",
            "note_ru": "Источник ограничил частоту запросов (HTTP 429)",
            "observations": [],
            "market_usable": False,
        }
    if fetched.unavailable or (fetched.error and not fetched.text):
        return {
            "connection_status": "UNAVAILABLE",
            "probe_result": "FAILED",
            "freshness": "UNAVAILABLE",
            "error": fetched.error or f"HTTP {fetched.status}",
            "note_ru": UNAVAILABLE_RU,
            "observations": [],
            "market_usable": False,
        }
    if fetched.blocked or fetched.status in {401, 403}:
        key_note = f" ({NEEDS_KEY_RU}: {key_env})" if key_env and not os.environ.get(key_env) else ""
        return {
            "connection_status": "NEEDS_KEY" if key_env and not os.environ.get(key_env) else "ERROR",
            "probe_result": "NEEDS_KEY" if key_env and not os.environ.get(key_env) else "BLOCKED",
            "freshness": "UNAVAILABLE",
            "error": f"HTTP {fetched.status}",
            "note_ru": BLOCKED_RU + key_note,
            "observations": [],
            "market_usable": False,
        }
    if fetched.status and fetched.status >= 400:
        return {
            "connection_status": "ERROR",
            "probe_result": "FAILED",
            "freshness": "UNAVAILABLE",
            "error": f"HTTP {fetched.status}",
            "note_ru": f"{UNAVAILABLE_RU} (HTTP {fetched.status})",
            "observations": [],
            "market_usable": False,
        }
    url = source_url or resolve_spec_url(spec)
    text = fetched.text or ""
    from services.agro_ops.series_parsers import parse_numeric_for_spec

    observations = parse_numeric_for_spec(spec, text, url)
    numeric = [o for o in observations if observation_is_numeric(o)]
    if numeric:
        note = f"Числовых наблюдений: {len(numeric)}"
        usable = True
        if str(spec.get("source_class") or spec.get("source_type")) == "UNKNOWN":
            usable = False
            for row in numeric:
                row["source_class"] = "UNKNOWN"
                row["trust_level"] = spec.get("trust_level") or "LOW"
                row["market_usable"] = False
            note += ". UNKNOWN: не используется в high-confidence анализе."
        if key_env and spec.get("id") == "usda_wasde" and not os.environ.get(key_env):
            note += f". FAS Open Data по-прежнему {NEEDS_KEY_RU} ({key_env})."
        return {
            "connection_status": "CONNECTED",
            "probe_result": "CONNECTED",
            "freshness": "LIVE",
            "error": "",
            "note_ru": note,
            "observations": numeric,
            "market_usable": usable,
        }
    metadata = _parse_legacy_metadata(spec, text, url)
    html_obs = _parse_html_signals(text, spec["id"], url) if _html_reachable(text) or "<html" in text.lower() else []
    observations = metadata or html_obs
    for row in observations:
        row.setdefault("data_class", "metadata")
        row["market_usable"] = False
        row.setdefault("normalized_value", None)
    if observations or (fetched.status == 200 and (_html_reachable(text) or html_obs or len(text) > 40)):
        extra = ""
        if spec.get("id") == "usda_wasde" and key_env and not os.environ.get(key_env):
            extra = f" Числовой FAS API: {NEEDS_KEY_RU} ({key_env}). Cornell/ESMIS JSON не содержит балансовых тонн."
        note = (
            "Каталог/метаданные получены, числовой ряд не разобран."
            if metadata
            else PARTIAL_RU
        ) + extra
        return {
            "connection_status": "DEGRADED",
            "probe_result": "PARTIAL",
            "freshness": "DELAYED",
            "error": "",
            "note_ru": PARTIAL_RU + extra,
            "observations": observations,
            "market_usable": False,
        }
    return {
        "connection_status": "ERROR",
        "probe_result": "UNAVAILABLE",
        "freshness": "UNAVAILABLE",
        "error": f"HTTP {fetched.status or 0}",
        "note_ru": UNAVAILABLE_RU,
        "observations": [],
        "market_usable": False,
    }


class AgroOpsProviderMixin:
    """Mixed into AgroOpsService — probe, ingest, health."""

    _fetch_override: FetchFn | None = None

    def set_provider_fetch(self, fn: FetchFn | None) -> None:
        self._fetch_override = fn

    async def _fetch_url(self, url: str, spec: dict[str, Any] | None = None) -> SimpleFetchResult:
        fn = self._fetch_override or default_fetch
        kwargs: dict[str, Any] = {}
        if spec:
            if spec.get("timeout_sec") is not None:
                kwargs["timeout_sec"] = spec["timeout_sec"]
            if spec.get("retries") is not None:
                kwargs["retries"] = spec["retries"]
        try:
            result = await fn(url, None, **kwargs)  # type: ignore[misc]
        except TypeError:
            result = await fn(url, None)
        if isinstance(result, SimpleFetchResult):
            return result
        return SimpleFetchResult(
            status=getattr(result, "status", 0),
            text=getattr(result, "text", "") or "",
            headers=getattr(result, "headers", {}) or {},
            error=getattr(result, "error", None),
            blocked=bool(getattr(result, "blocked", False)),
            unavailable=bool(getattr(result, "unavailable", False)),
            timed_out=bool(getattr(result, "timed_out", False)),
            rate_limited=bool(getattr(result, "rate_limited", False)),
            content_type=str(getattr(result, "content_type", "") or ""),
        )

    def _provider_row(self, spec: dict[str, Any], stored: dict[str, Any] | None) -> dict[str, Any]:
        stored = stored or {}
        fixed = spec.get("fixed_status")
        if fixed == "CONNECTED":
            status, freshness, note = "CONNECTED", "LIVE", "Доступен: данные вводятся вручную или импортируются"
        elif stored.get("connection_status"):
            status = str(stored.get("connection_status"))
            freshness = str(stored.get("freshness") or status)
            note = str(stored.get("note_ru") or "")
        elif spec.get("source_type") == "licensed" or spec.get("needs_key") or fixed == "NEEDS_KEY":
            status, freshness, note = "NEEDS_KEY", "NOT_CONFIGURED", NEEDS_KEY_RU
        elif fixed == "NOT_CONFIGURED":
            status, freshness, note = "NOT_CONFIGURED", "NOT_CONFIGURED", NOT_SETUP_RU
        else:
            status, freshness, note = "NOT_CONFIGURED", "NOT_CONFIGURED", NOT_CONFIGURED_RU
        last_success = stored.get("last_success_at")
        if status == "CONNECTED" and last_success:
            try:
                ts = datetime.fromisoformat(str(last_success).replace("Z", "+00:00"))
                if datetime.now(timezone.utc) - ts > timedelta(hours=72):
                    status, freshness = "STALE", "STALE"
                    note = "Данные устарели — требуется повторная проверка"
            except Exception:
                pass
        numeric_n = int(stored.get("numeric_count") or 0)
        meta_n = int(stored.get("metadata_count") or 0)
        usable = bool(stored.get("market_usable")) if "market_usable" in stored else numeric_n > 0
        data_type = stored.get("data_type_ru") or (
            "Числовой ряд" if usable else (
                "Метаданные" if (stored.get("observation_count") or meta_n) else (
                    "Ручной ввод" if spec.get("source_type") == "manual" else "Нет данных"
                )
            )
        )
        if spec.get("source_type") == "manual":
            data_type = "Ручной ввод"
        hs = str(stored.get("health_state") or health_state(status, stored.get("probe_result")))
        if spec.get("id") == "weather_provider_secondary" and hs in {
            "NEEDS_KEY",
            "REQUIRES_CONFIGURATION",
            "NOT_CONFIGURED",
            "NEEDS_LICENSE",
        }:
            hs = "OPTIONAL_NOT_CONFIGURED"
        elif spec.get("source_type") == "licensed" and hs in {"NEEDS_KEY", "REQUIRES_CONFIGURATION"}:
            hs = "NEEDS_LICENSE"
        elif hs == "PARTIAL" and numeric_n == 0:
            hs = "METADATA_ONLY"
        if str(spec.get("source_class") or stored.get("source_class") or "") == "UNKNOWN":
            usable = False
        return {
            "id": spec["id"],
            "provider_id": spec["id"],
            "name": spec["label_ru"],
            "label_ru": spec["label_ru"],
            "category": spec["category"],
            "group": next((c["group"] for c in PROVIDER_CATALOG if c["id"] == spec["id"]), spec["category"]),
            "kind": spec["category"],
            "country": spec["country"],
            "region": spec["region"],
            "source_type": spec["source_type"],
            "data_type": data_type,
            "data_type_ru": data_type,
            "official": spec["official"],
            "priority": spec["priority"],
            "url": spec["url"],
            "license_note_ru": spec["license_note_ru"],
            "receives_ru": spec["receives_ru"],
            "cadence": spec["cadence"],
            "status": "LIVE" if status == "CONNECTED" and spec["id"] == "manual_import" else status,
            "connection_status": status,
            "freshness": freshness,
            "freshness_ru": freshness,
            "note_ru": note,
            "error": stored.get("error") or stored.get("last_error") or "",
            "last_success_at": last_success,
            "last_attempt_at": stored.get("last_attempt_at"),
            "next_check_at": stored.get("next_check_at"),
            "observation_count": stored.get("observation_count") or 0,
            "numeric_count": numeric_n,
            "metadata_count": meta_n,
            "market_usable": usable,
            "adapter_type": spec.get("source_type"),
            "health_state": hs,
            "health_color": HEALTH_COLORS.get(hs, "gray"),
            "raw_excerpt": stored.get("raw_excerpt") or "",
        }

    async def providers_status(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        bag = self._bag(org)  # type: ignore[attr-defined]
        stored = {str(s.get("provider_id")): s for s in active_only(bag.get("intel_source") or [])}
        items = [self._provider_row(spec, stored.get(spec["id"])) for spec in PROVIDER_SPECS]
        for row in active_only(bag.get("intel_source") or []):
            if not row.get("custom"):
                continue
            spec = {
                "id": str(row.get("provider_id") or row.get("id")),
                "label_ru": row.get("label_ru") or row.get("name") or row.get("url"),
                "category": "manual",
                "country": row.get("country") or "ORG",
                "region": row.get("region") or "",
                "source_type": row.get("source_class") or "UNKNOWN",
                "official": str(row.get("source_class") or "") in {"OFFICIAL_API", "PUBLIC_DATA"},
                "priority": 3,
                "url": row.get("url") or "",
                "license_note_ru": f"Пользовательский URL, trust={row.get('trust_level') or 'LOW'}",
                "receives_ru": "Добавленный администратором источник",
                "cadence": "on_demand",
            }
            extra = self._provider_row(spec, row)
            extra["custom"] = True
            extra["source_class"] = row.get("source_class")
            extra["trust_level"] = row.get("trust_level")
            extra["health_color"] = HEALTH_COLORS.get(str(extra.get("health_state")), "gray")
            if str(row.get("source_class")) == "UNKNOWN":
                extra["market_usable"] = False
            items.append(extra)
        return {
            "ok": True,
            "items": items,
            "freshness_statuses": list(CONNECTION_STATUSES),
            "connection_statuses": list(CONNECTION_STATUSES),
        }

    async def probe_provider(
        self, organization_id: str, provider_id: str, role: str | None = None, *, persist: bool = True
    ) -> dict[str, Any]:
        denied = require(role, "intel")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        spec = _spec(provider_id) or self._custom_spec(org, provider_id)
        if not spec:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный источник"}
        fetched = SimpleFetchResult()
        observations: list[dict[str, Any]] = []
        interpreted: dict[str, Any] = {}
        if spec.get("url") and spec.get("fixed_status") not in {"NOT_CONFIGURED", "NEEDS_KEY", "CONNECTED"}:
            primary_url = resolve_spec_url(spec)
            extra_urls = list(spec.get("extra_urls") or [])
            if spec.get("prefer_extra_urls"):
                interpreted = {
                    "connection_status": "ERROR",
                    "probe_result": "FAILED",
                    "freshness": "UNAVAILABLE",
                    "error": "",
                    "note_ru": "",
                    "observations": [],
                    "market_usable": False,
                }
                for extra in extra_urls:
                    extra_url = extra if isinstance(extra, str) else str(extra.get("url") or "")
                    if not extra_url:
                        continue
                    extra_fetched = await self._fetch_url(resolve_spec_url(spec, extra_url), spec)
                    extra_interp = interpret_fetch(spec, extra_fetched, source_url=extra_url)
                    extra_obs = extra_interp.get("observations") or []
                    if extra_obs:
                        observations.extend(extra_obs)
                        fetched = extra_fetched
                        if extra_interp.get("probe_result") == "CONNECTED":
                            interpreted = extra_interp
                extra_urls = []
            fetched = await self._fetch_url(primary_url, spec)
            if fetched.unavailable or fetched.blocked or fetched.timed_out or (fetched.status and fetched.status >= 400):
                for alt in spec.get("fallback_urls") or []:
                    alt_fetched = await self._fetch_url(resolve_spec_url(spec, str(alt)), spec)
                    if not alt_fetched.unavailable and not alt_fetched.blocked and not alt_fetched.timed_out and alt_fetched.status and alt_fetched.status < 400:
                        fetched = alt_fetched
                        primary_url = resolve_spec_url(spec, str(alt))
                        break
            primary_interp = interpret_fetch(spec, fetched, source_url=primary_url)
            if not interpreted:
                interpreted = primary_interp
            primary_obs = list(primary_interp.get("observations") or [])
            if primary_obs:
                observations.extend(primary_obs)
                if primary_interp.get("probe_result") == "CONNECTED":
                    interpreted = primary_interp
            elif interpreted.get("probe_result") != "CONNECTED":
                interpreted = primary_interp
            for extra in extra_urls:
                extra_url = extra if isinstance(extra, str) else str(extra.get("url") or "")
                if not extra_url:
                    continue
                extra_fetched = await self._fetch_url(resolve_spec_url(spec, extra_url), spec)
                extra_interp = interpret_fetch(spec, extra_fetched, source_url=extra_url)
                extra_obs = extra_interp.get("observations") or []
                if extra_obs:
                    observations.extend(extra_obs)
                    if extra_interp.get("probe_result") == "CONNECTED":
                        interpreted["probe_result"] = "CONNECTED"
                        interpreted["connection_status"] = "CONNECTED"
                        interpreted["market_usable"] = True
            numeric_now = [o for o in observations if observation_is_numeric(o)]
            unknown = str(spec.get("source_class") or spec.get("source_type") or "") == "UNKNOWN" or str(
                spec.get("trust_level") or ""
            ).upper() == "LOW"
            if numeric_now and unknown:
                interpreted["probe_result"] = "PARTIAL"
                interpreted["connection_status"] = "DEGRADED"
                interpreted["market_usable"] = False
                interpreted["note_ru"] = (
                    "Источник UNKNOWN/LOW: значения сохранены, но не входят в high-confidence анализ."
                )
            elif numeric_now:
                interpreted["probe_result"] = "CONNECTED"
                interpreted["connection_status"] = "CONNECTED"
                interpreted["market_usable"] = True
                interpreted["freshness"] = "LIVE"
                interpreted["error"] = ""
                note = f"Числовых наблюдений: {len(numeric_now)}"
                qcl_ok = any(str(o.get("series_id") or "").startswith("faostat-") and o.get("series_kind") == "production" for o in numeric_now)
                fpi_ok = any(str(o.get("series_id") or "") == "faostat-fpi-cereals" for o in numeric_now)
                if spec.get("id") == "fao" and fpi_ok and not qcl_ok:
                    note += (
                        ". FAOSTAT QCL (тонны производства) недоступен: fenixservices.fao.org timeout/HTTP 521. "
                        "Подключён официальный FAO Food Price Index CSV (Cereals), не тонны QCL."
                    )
                interpreted["note_ru"] = note
            interpreted["observations"] = observations
        else:
            interpreted = interpret_fetch(spec, fetched)
        numeric_n = len([o for o in observations if observation_is_numeric(o)])
        meta_n = len(observations) - numeric_n
        now = _now()
        next_check = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
        row = {
            "provider_id": provider_id,
            "connected": interpreted["connection_status"] == "CONNECTED",
            "connection_status": interpreted["connection_status"],
            "freshness": interpreted["freshness"],
            "note_ru": interpreted["note_ru"],
            "error": interpreted["error"],
            "last_error": interpreted["error"],
            "last_attempt_at": now,
            "last_success_at": now if interpreted["connection_status"] in {"CONNECTED", "DEGRADED"} else None,
            "next_check_at": next_check,
            "observation_count": len(interpreted["observations"]),
            "numeric_count": numeric_n,
            "metadata_count": meta_n,
            "market_usable": False
            if str(spec.get("source_class") or spec.get("source_type") or "") == "UNKNOWN"
            or str(spec.get("trust_level") or "").upper() == "LOW"
            else (bool(interpreted.get("market_usable")) or numeric_n > 0),
            "data_type_ru": "Числовой ряд" if numeric_n else ("Метаданные" if observations else "Нет данных"),
            "url": resolve_spec_url(spec),
            "probe_result": interpreted["probe_result"],
            "adapter_type": spec.get("source_type"),
            "raw_excerpt": (fetched.text or "")[:2000],
            "http_status": fetched.status,
        }
        snapshot = None
        raw = None
        if persist:
            raw = await self._store_raw(org, spec, fetched, role)
            snapshot = await self._store_probe(org, spec, row, interpreted, role)
        return {
            "ok": True,
            "item": {**self._provider_row(spec, row), **row, "probe_result": interpreted["probe_result"]},
            "observations": interpreted["observations"],
            "snapshot": snapshot,
            "raw": raw,
        }

    async def _store_raw(
        self, org: str, spec: dict[str, Any], fetched: SimpleFetchResult, role: str | None
    ) -> dict[str, Any] | None:
        from services.agro_ops.service import active_only

        body = fetched.text or fetched.error or ""
        digest = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
        bag = self._bag(org)  # type: ignore[attr-defined]
        existing = next((r for r in active_only(bag.get("provider_raw") or []) if r.get("content_hash") == digest), None)
        if existing:
            return existing
        file_ref = ""
        if len(body) > 4000:
            import os
            from pathlib import Path

            root = Path(os.environ.get("AGRO_OPS_RAW_DIR") or os.path.join(os.getcwd(), "data", "agro_ops_raw"))
            dest_dir = root / org
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / digest[:24]
            dest.write_text(body[:400_000], encoding="utf-8")
            file_ref = str(dest)
        saved = await self.create_entity(  # type: ignore[attr-defined]
            org,
            "provider_raw",
            {
                "name": f"RAW {spec['label_ru']}",
                "provider_id": spec["id"],
                "request_url": spec.get("url") or "",
                "retrieved_at": _now(),
                "http_status": fetched.status,
                "content_type": fetched.content_type or "",
                "content_hash": digest,
                "file_ref": file_ref,
                "payload_excerpt": body[:2000],
                "byte_length": len(body.encode("utf-8", errors="replace")),
            },
            role or "platform_owner",
        )
        return saved.get("item") if isinstance(saved, dict) else saved

    async def _store_probe(
        self,
        org: str,
        spec: dict[str, Any],
        row: dict[str, Any],
        interpreted: dict[str, Any],
        role: str | None,
    ) -> dict[str, Any]:
        from services.agro_ops.service import active_only

        bag = self._bag(org)  # type: ignore[attr-defined]
        existing = next(
            (s for s in bag.get("intel_source") or [] if str(s.get("provider_id")) == spec["id"] and not s.get("archived_at")),
            None,
        )
        if existing:
            preserved = {
                k: existing.get(k)
                for k in ("custom", "source_class", "trust_level")
                if existing.get(k) is not None
            }
            await self.update_entity(org, "intel_source", str(existing["id"]), {**preserved, **row}, role or "platform_owner")  # type: ignore[attr-defined]
        else:
            extra = {
                k: spec.get(k)
                for k in ("custom", "source_class", "trust_level")
                if spec.get(k) is not None
            }
            await self.create_entity(org, "intel_source", {**row, "name": spec["label_ru"], **extra}, role or "platform_owner")  # type: ignore[attr-defined]
        snap = {
            "name": f"Снимок {spec['label_ru']}",
            "provider_id": spec["id"],
            "source_url": spec.get("url"),
            "observed_at": _now(),
            "published_at": _now(),
            "ingested_at": _now(),
            "connection_status": row["connection_status"],
            "probe_result": interpreted["probe_result"],
            "note_ru": row["note_ru"],
            "error": row["error"],
            "observation_count": row["observation_count"],
            "adapter_type": spec.get("source_type"),
            "raw_excerpt": row.get("raw_excerpt") or "",
            "http_status": row.get("http_status"),
            "fingerprint": fingerprint(spec["id"], row["connection_status"], row["observation_count"], row.get("last_attempt_at")),
        }
        saved_snap = await self.create_entity(org, "provider_snapshot", snap, role or "platform_owner")  # type: ignore[attr-defined]
        kind = str(spec.get("observation_kind") or "market_observation")
        stored = 0
        for obs in interpreted["observations"]:
            series_kind = str(obs.get("series_kind") or "")
            kind = {
                "price": "price_observation",
                "fx": "price_observation",
                "weather": "weather_observation",
                "trade": "trade_observation",
                "production": "crop_observation",
                "yield": "crop_observation",
                "area": "crop_observation",
            }.get(series_kind, str(spec.get("observation_kind") or "market_observation"))
            fp = fingerprint(
                spec["id"],
                obs.get("source_reference"),
                obs.get("raw_value"),
                obs.get("title"),
                obs.get("commodity"),
                obs.get("normalized_value"),
                obs.get("observed_at"),
                obs.get("series_id"),
            )
            bag = self._bag(org)  # type: ignore[attr-defined]
            if any(x.get("fingerprint") == fp for x in bag.get(kind) or []):
                continue
            payload = normalize_observation(
                {
                    **obs,
                    "name": obs.get("title") or obs.get("raw_value") or spec["label_ru"],
                    "freshness": row["freshness"],
                    "fingerprint": fp,
                },
                spec,
                _now(),
            )
            await self.create_entity(org, kind, payload, role or "platform_owner")  # type: ignore[attr-defined]
            stored += 1
        item = saved_snap.get("item") if isinstance(saved_snap, dict) else saved_snap
        if isinstance(item, dict):
            item["stored_observations"] = stored
        return item if isinstance(item, dict) else {"stored_observations": stored}

    async def ingest_providers(
        self, organization_id: str | None = None, role: str | None = "platform_owner", *, cadence: str | None = None
    ) -> dict[str, Any]:
        from services.agro_ops.service import _org

        org = _org(organization_id)
        results = []
        for spec in PROVIDER_SPECS:
            if spec.get("fixed_status") in {"NOT_CONFIGURED", "NEEDS_KEY"}:
                continue
            if cadence == "weather" and spec["category"] != "weather":
                continue
            if cadence == "light" and spec["id"] not in {"weather_provider", "fx_rates"}:
                continue
            if cadence == "markets" and spec["category"] not in {"prices", "eu_market", "world_balance", "trade"}:
                continue
            if spec["id"] == "manual_import":
                continue
            try:
                probed = await self.probe_provider(org, spec["id"], role, persist=True)
            except Exception as exc:
                results.append(
                    {
                        "provider_id": spec["id"],
                        "ok": False,
                        "connection_status": "ERROR",
                        "probe_result": "FAILED",
                        "note_ru": f"Сбой источника: {exc}"[:240],
                    }
                )
                continue
            results.append(
                {
                    "provider_id": spec["id"],
                    "ok": bool(probed.get("ok")),
                    "connection_status": (probed.get("item") or {}).get("connection_status"),
                    "probe_result": (probed.get("item") or {}).get("probe_result"),
                    "note_ru": (probed.get("item") or {}).get("note_ru"),
                    "http_status": (probed.get("item") or {}).get("http_status"),
                    "observation_count": (probed.get("item") or {}).get("observation_count") or 0,
                    "numeric_count": (probed.get("item") or {}).get("numeric_count") or 0,
                    "market_usable": (probed.get("item") or {}).get("market_usable"),
                }
            )
        try:
            await self.evaluate_alerts(org, role)  # type: ignore[attr-defined]
        except Exception:
            pass
        return {"ok": True, "organization_id": org, "items": results}

    async def refresh_all_providers(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "intel")
        if denied:
            return denied
        return await self.run_pipeline(  # type: ignore[attr-defined]
            organization_id,
            role,
            fetch="full",
            analysis_type=None,
            reports=["morning", "evening"],
            record_full_refresh=True,
        )

    def _refresh_meta_row(self, org: str) -> dict[str, Any] | None:
        from services.agro_ops.service import active_only

        return next(
            (
                s
                for s in active_only(self._bag(org).get("settings") or [])  # type: ignore[attr-defined]
                if s.get("refresh_meta")
            ),
            None,
        )

    async def _save_refresh_meta(self, org: str, role: str | None, *, duration_sec: float) -> None:
        from services.agro_ops.analytics import _now

        payload = {
            "name": "agro-refresh-meta",
            "title": "Последнее полное обновление источников",
            "refresh_meta": True,
            "last_full_refresh_at": _now(),
            "last_full_refresh_duration_sec": duration_sec,
        }
        existing = self._refresh_meta_row(org)
        try:
            if existing:
                await self.update_entity(org, "settings", str(existing["id"]), payload, role or "agro_director")  # type: ignore[attr-defined]
            else:
                await self.create_entity(org, "settings", payload, role or "agro_director")  # type: ignore[attr-defined]
        except Exception:
            bag = self._bag(org)  # type: ignore[attr-defined]
            row = {**payload, "id": (existing or {}).get("id") or str(uuid.uuid4()), "status": "active"}
            if existing:
                existing.update(row)
            else:
                bag.setdefault("settings", []).insert(0, row)


    def _custom_spec(self, org: str, provider_id: str) -> dict[str, Any] | None:
        from services.agro_ops.service import active_only

        row = next(
            (
                s
                for s in active_only(self._bag(org).get("intel_source") or [])  # type: ignore[attr-defined]
                if s.get("custom") and str(s.get("provider_id") or s.get("id")) == str(provider_id)
            ),
            None,
        )
        if not row:
            return None
        return {
            "id": str(row.get("provider_id") or row.get("id")),
            "label_ru": row.get("label_ru") or row.get("name") or "Пользовательский источник",
            "category": "manual",
            "country": "ORG",
            "region": "",
            "source_type": row.get("source_class") or "UNKNOWN",
            "source_class": row.get("source_class") or "UNKNOWN",
            "trust_level": row.get("trust_level") or "LOW",
            "official": str(row.get("source_class") or "") in {"OFFICIAL_API", "PUBLIC_DATA"},
            "priority": 3,
            "url": row.get("url") or "",
            "license_note_ru": "",
            "receives_ru": "Пользовательский URL",
            "cadence": "on_demand",
        }

    async def add_custom_source(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "intel")
        if denied:
            return denied
        from services.agro_ops.service import _org

        url = str(body.get("url") or "").strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            return {"ok": False, "error": "validation", "message_ru": "Укажите http(s) URL"}
        source_class = str(body.get("source_class") or classify_source_url(url))
        if source_class not in {"OFFICIAL_API", "PUBLIC_DATA", "RSS", "MANUAL_SOURCE", "UNKNOWN"}:
            source_class = classify_source_url(url)
        trust = str(body.get("trust_level") or ("HIGH" if source_class == "OFFICIAL_API" else "MEDIUM" if source_class == "PUBLIC_DATA" else "LOW")).upper()
        if trust not in {"HIGH", "MEDIUM", "LOW"}:
            trust = "LOW"
        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        pid = f"custom-{uuid.uuid4().hex[:10]}"
        row = {
            "provider_id": pid,
            "name": body.get("label_ru") or url,
            "label_ru": body.get("label_ru") or url,
            "url": url,
            "custom": True,
            "source_class": source_class,
            "trust_level": trust,
            "connection_status": "NOT_CONFIGURED",
            "probe_result": "NOT_CONFIGURED",
            "note_ru": f"Класс {source_class}, доверие {trust}. UNKNOWN не влияет на high-confidence анализ.",
            "market_usable": False,
        }
        saved = await self.create_entity(org, "intel_source", row, role or "platform_owner")  # type: ignore[attr-defined]
        item = saved.get("item") if isinstance(saved, dict) else saved
        return {"ok": True, "item": item, "source_class": source_class, "trust_level": trust}

    async def provider_detail(self, organization_id: str, provider_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        spec = _spec(provider_id)
        if not spec:
            from services.agro_ops.service import _org

            spec = self._custom_spec(_org(organization_id), provider_id)
        if not spec:
            return {"ok": False, "error": "not_found", "message_ru": "Источник не найден"}
        status = await self.providers_status(organization_id, role)
        item = next((i for i in status.get("items") or [] if i["id"] == provider_id), None)
        obs = await self.provider_observations(organization_id, role, {"provider_id": provider_id})
        return {
            "ok": True,
            "item": item,
            "observations": [o for o in obs.get("items") or [] if o.get("record_kind") not in {"provider_snapshot", "provider_raw"}],
            "snapshots": [o for o in obs.get("items") or [] if o.get("record_kind") == "provider_snapshot"],
            "raw": [o for o in obs.get("items") or [] if o.get("record_kind") == "provider_raw"],
            "receives_ru": spec.get("receives_ru"),
            "category": spec.get("category"),
        }

    async def provider_observations(
        self, organization_id: str, role: str | None = None, query: dict[str, str] | None = None
    ) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        bag = self._bag(org)  # type: ignore[attr-defined]
        kinds = (
            "market_observation",
            "trade_observation",
            "weather_observation",
            "crop_observation",
            "price_observation",
            "provider_snapshot",
            "provider_raw",
        )
        items: list[dict[str, Any]] = []
        for kind in kinds:
            for row in active_only(bag.get(kind) or []):
                items.append({**row, "record_kind": kind})
        q = query or {}
        if q.get("provider_id"):
            items = [i for i in items if str(i.get("provider_id")) == q["provider_id"]]
        if q.get("kind"):
            items = [i for i in items if str(i.get("record_kind")) == q["kind"]]
        items.sort(key=lambda i: str(i.get("ingested_at") or i.get("created_at") or ""), reverse=True)
        return {"ok": True, "items": items[:200]}

    def _scheduler_row(self, org: str) -> dict[str, Any] | None:
        from services.agro_ops.service import active_only

        return next(
            (
                s
                for s in active_only(self._bag(org).get("settings") or [])  # type: ignore[attr-defined]
                if s.get("scheduler_config")
            ),
            None,
        )

    async def get_scheduler(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        stored = self._scheduler_row(org)
        jobs = list((stored or {}).get("jobs") or DEFAULT_AGRO_SCHEDULE["jobs"])
        by_id = {str(j.get("id")): j for j in jobs}
        merged = []
        for default in DEFAULT_AGRO_SCHEDULE["jobs"]:
            override = by_id.get(str(default["id"])) or {}
            merged.append({**default, **{k: v for k, v in override.items() if v not in (None, "")}})
        from services.agro_ops.presentation import present_schedule

        return {
            "ok": True,
            "timezone": str((stored or {}).get("timezone") or DEFAULT_AGRO_SCHEDULE["timezone"]),
            "jobs": merged,
            "jobs_human": present_schedule(merged),
            "configurable": True,
        }

    async def put_scheduler(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "intel_admin")
        if denied:
            denied = require(role, "admin")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        incoming = body.get("jobs") if isinstance(body.get("jobs"), list) else DEFAULT_AGRO_SCHEDULE["jobs"]
        from services.agro_ops.presentation import cron_to_human

        normalized = []
        for job in incoming:
            row = dict(job)
            time_kyiv = str(row.get("time_kyiv") or "").strip()
            if time_kyiv and ":" in time_kyiv:
                hh, mm = time_kyiv.split(":")[:2]
                existing_cron = str(row.get("cron_kyiv") or "0 0 * * *")
                human = cron_to_human(existing_cron)
                when = str(row.get("when_ru") or human.get("when_ru") or "")
                parts = existing_cron.split()
                dom = parts[2] if len(parts) >= 5 else "*"
                dow = parts[4] if len(parts) >= 5 else "*"
                if "воскрес" in when:
                    row["cron_kyiv"] = f"{int(mm)} {int(hh)} * * 0"
                elif "1-е" in when or "1-e" in when:
                    row["cron_kyiv"] = f"{int(mm)} {int(hh)} 1 * *"
                else:
                    row["cron_kyiv"] = f"{int(mm)} {int(hh)} {dom} * {dow}"
            normalized.append(row)
        incoming = normalized
        timezone = str(body.get("timezone") or "Europe/Kyiv")
        payload = {
            "name": "agro-scheduler",
            "title": "Расписание агро-разведки",
            "scheduler_config": True,
            "timezone": timezone,
            "jobs": incoming,
        }
        existing = self._scheduler_row(org)
        if existing:
            saved = await self.update_entity(org, "settings", str(existing["id"]), payload, role or "agro_director")  # type: ignore[attr-defined]
        else:
            saved = await self.create_entity(org, "settings", payload, role or "agro_director")  # type: ignore[attr-defined]
        item = saved.get("item") if isinstance(saved, dict) else saved
        refreshed = await self.get_scheduler(org, role)
        return {**refreshed, "item": item}
