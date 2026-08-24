"""AGRO 1.6 — parsers for official numeric series.

HTTP 200 is not enough. A row is numeric only when `normalized_value` is a finite float.
No invented prices, tonnes, weather, or FX.
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_finite_number(value: Any) -> bool:
    if value in (None, "", False, True):
        return False
    try:
        number = float(str(value).replace(" ", "").replace("\u00a0", "").replace(",", "."))
    except (TypeError, ValueError):
        return False
    return math.isfinite(number)


def to_float(value: Any) -> float | None:
    if not is_finite_number(value):
        return None
    text = str(value).strip()
    text = re.sub(r"[^\d,.\-]", "", text)
    if not text or text in {".", "-", ",", "-.", "-,"}:
        return None
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def parse_euro_price(value: Any) -> float | None:
    """EC Agri-food prices look like '€288,37'."""
    if value in (None, ""):
        return None
    text = str(value).replace("€", "").replace("EUR", "").strip()
    return to_float(text)


def numeric_observation(
    *,
    provider_id: str,
    source_url: str,
    title: str,
    value: float,
    unit: str,
    series_id: str,
    series_kind: str,
    observed_at: str,
    commodity: str = "",
    country: str = "",
    currency: str = "",
    source_reference: str = "",
    sections: tuple[str, ...] | list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "provider_id": provider_id,
        "source_url": source_url,
        "source_reference": source_reference or series_id,
        "published_at": observed_at,
        "observed_at": observed_at,
        "country": country,
        "commodity": commodity,
        "unit": unit,
        "currency": currency,
        "raw_value": value,
        "value": value,
        "normalized_value": float(value),
        "confidence": "high",
        "title": title,
        "data_class": "numeric",
        "market_usable": True,
        "series_id": series_id,
        "series_kind": series_kind,
        "canonical_type": {
            "price": "AgroPriceObservation",
            "fx": "AgroPriceObservation",
            "weather": "AgroWeatherObservation",
            "trade": "AgroTradeObservation",
            "production": "AgroProductionObservation",
            "yield": "AgroProductionObservation",
            "area": "AgroProductionObservation",
        }.get(series_kind, "AgroIntelligenceItem"),
        "sections": list(sections or ()),
    }
    if extra:
        row.update(extra)
    return row


def _load_json(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return None


def parse_ec_cereal_prices(text: str, provider_id: str, source_url: str) -> list[dict[str, Any]]:
    body = _load_json(text)
    rows = body if isinstance(body, list) else (body.get("prices") if isinstance(body, dict) else None)
    if not isinstance(rows, list):
        return []
    out: list[dict[str, Any]] = []
    for row in rows[:40]:
        if not isinstance(row, dict):
            continue
        price = parse_euro_price(row.get("price"))
        if price is None:
            continue
        product = str(row.get("productName") or row.get("product") or "Cereal").strip()
        state = str(row.get("memberStateCode") or row.get("memberStateName") or "EU")
        begin = str(row.get("beginDate") or row.get("endDate") or "")
        observed = _iso_from_eu_date(begin) or _now()
        unit = str(row.get("unit") or "TONNES")
        display_unit = "EUR/t" if unit.upper() in {"TONNES", "T", "MT"} else unit
        out.append(
            numeric_observation(
                provider_id=provider_id,
                source_url=source_url,
                title=f"{product} {state} {price} {display_unit} ({begin or observed[:10]})",
                value=price,
                unit=display_unit,
                series_id=f"ec-cereal-{state}-{product}",
                series_kind="price",
                observed_at=observed,
                commodity=product,
                country=state,
                currency="EUR",
                source_reference=f"{state}|{product}|{begin}",
                sections=("prices", "world"),
            )
        )
    return out


def _iso_from_eu_date(value: str) -> str | None:
    raw = (value or "").strip()
    if not raw:
        return None
    for fmt in ("%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw[:10], fmt).replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue
    return None


def parse_eurostat_sdmx(text: str, provider_id: str, source_url: str) -> list[dict[str, Any]]:
    body = _load_json(text)
    if not isinstance(body, dict) or not isinstance(body.get("value"), dict):
        return []
    values = body["value"]
    if not values:
        return []
    ids = body.get("id") or []
    sizes = body.get("size") or []
    dimensions = body.get("dimension") or {}
    if not isinstance(ids, list) or not isinstance(sizes, list) or not isinstance(dimensions, dict):
        return []
    indexes: list[dict[str, str]] = []
    labels: list[dict[str, str]] = []
    for dim_id, size in zip(ids, sizes):
        cat = ((dimensions.get(dim_id) or {}).get("category") or {})
        idx = cat.get("index") or {}
        lab = cat.get("label") or {}
        inverse = {int(v): str(k) for k, v in idx.items()} if isinstance(idx, dict) else {}
        indexes.append({str(i): inverse.get(i, str(i)) for i in range(int(size or 0))})
        labels.append({str(k): str(v) for k, v in (lab.items() if isinstance(lab, dict) else [])})

    def coords(linear: int) -> dict[str, str]:
        remaining = int(linear)
        parts: list[int] = []
        for size in reversed([int(s or 1) for s in sizes]):
            size = max(1, size)
            parts.append(remaining % size)
            remaining //= size
        parts.reverse()
        out: dict[str, str] = {}
        for dim_id, pos, imap in zip(ids, parts, indexes):
            out[str(dim_id)] = imap.get(str(pos), str(pos))
        return out

    kind_map = {
        "AR": ("area", "1000 ha"),
        "AR_THS_HA": ("area", "1000 ha"),
        "PR_HU_EU": ("production", "1000 t"),
        "PR": ("production", "1000 t"),
        "PR_THS_T": ("production", "1000 t"),
        "YI_HU_EU": ("yield", "100 kg/ha"),
        "YI": ("yield", "t/ha"),
        "YI_T_HA": ("yield", "t/ha"),
    }
    out: list[dict[str, Any]] = []
    preferred_geo = {"FR", "DE", "PL", "HU", "RO", "IT", "ES", "BG", "EU27_2020", "EU"}
    for key, raw in values.items():
        number = to_float(raw)
        if number is None:
            continue
        try:
            linear = int(key)
        except (TypeError, ValueError):
            continue
        dim = coords(linear)
        geo = dim.get("geo") or "EU"
        if preferred_geo and geo not in preferred_geo and len(out) >= 12:
            continue
        if geo not in preferred_geo and len([o for o in out if o.get("country") not in preferred_geo]) >= 4:
            continue
        year = dim.get("time") or dim.get("TIME_PERIOD") or ""
        crop_code = dim.get("crops") or ""
        crop_label = labels[ids.index("crops")].get(crop_code, crop_code) if "crops" in ids else "Wheat"
        struct = dim.get("strucpro") or ""
        if struct in kind_map:
            series_kind, unit = kind_map[struct]
        elif struct.startswith("AR"):
            series_kind, unit = "area", "1000 ha"
        elif struct.startswith("YI"):
            series_kind, unit = "yield", "t/ha"
        elif struct.startswith("PR"):
            series_kind, unit = "production", "1000 t"
        else:
            series_kind, unit = "production", "Eurostat"
        observed = f"{year}-01-01T00:00:00+00:00" if re.fullmatch(r"\d{4}", str(year)) else _now()
        title = f"{crop_label} {geo} {series_kind} {number} {unit} ({year})"
        out.append(
            numeric_observation(
                provider_id=provider_id,
                source_url=source_url,
                title=title,
                value=number,
                unit=unit,
                series_id=f"eurostat-tag00047-{geo}-{struct or series_kind}",
                series_kind=series_kind,
                observed_at=observed,
                commodity=str(crop_label),
                country=geo,
                source_reference=f"{geo}|{struct}|{year}|{crop_code}",
                sections=("harvest", "world") if series_kind != "price" else ("prices", "world"),
            )
        )
        if len(out) >= 36:
            break
    return out


_FPI_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def _fpi_observed_at(date_raw: str) -> str:
    text = (date_raw or "").strip()
    match = re.fullmatch(r"([A-Za-z]{3})-(\d{2}|\d{4})", text)
    if match:
        month = _FPI_MONTHS.get(match.group(1).lower())
        year_raw = match.group(2)
        if month:
            year = int(year_raw)
            if year < 100:
                year += 1900 if year >= 70 else 2000
            return f"{year:04d}-{month:02d}-01T00:00:00+00:00"
    for fmt in ("%Y-%m", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(text, fmt)
            return f"{dt.year:04d}-{dt.month:02d}-01T00:00:00+00:00"
        except ValueError:
            continue
    return _now()


def parse_fao_food_price_index(text: str, provider_id: str, source_url: str) -> list[dict[str, Any]]:
    """Official FAO Food Price Index CSV (same FPI series published on FAOSTAT)."""
    import csv
    import io

    raw = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = raw.split("\n")
    header_idx = next(
        (
            i
            for i, line in enumerate(lines)
            if line.lower().lstrip().startswith("date,") and "cereal" in line.lower()
        ),
        None,
    )
    if header_idx is None:
        return []
    reader = csv.DictReader(io.StringIO("\n".join(lines[header_idx:])))
    out: list[dict[str, Any]] = []
    for row in reader:
        if not isinstance(row, dict):
            continue
        date_raw = str(row.get("Date") or row.get("date") or "").strip()
        cereals = None
        for key, value in row.items():
            if key and "cereal" in key.lower():
                cereals = to_float(value)
                break
        if cereals is None or not date_raw:
            continue
        observed = _fpi_observed_at(date_raw)
        out.append(
            numeric_observation(
                provider_id=provider_id,
                source_url=source_url,
                title=f"FAO Food Price Index (FAOSTAT/FPI) — Cereals {cereals} (index, {date_raw})",
                value=cereals,
                unit="index",
                series_id="faostat-fpi-cereals",
                series_kind="price",
                observed_at=observed,
                commodity="Cereals",
                country="INTL",
                source_reference=f"FPI|Cereals|{date_raw}",
                sections=("prices", "world"),
            )
        )
    out.sort(key=lambda r: str(r.get("observed_at") or ""))
    return out[-24:]


def parse_faostat_data(text: str, provider_id: str, source_url: str) -> list[dict[str, Any]]:
    body = _load_json(text)
    if not isinstance(body, dict):
        return []
    data = body.get("data")
    if not isinstance(data, list):
        return []
    out: list[dict[str, Any]] = []
    for row in data[:40]:
        if not isinstance(row, dict):
            continue
        number = to_float(row.get("Value") or row.get("value"))
        if number is None:
            continue
        item = str(row.get("Item") or row.get("item") or "Crop")
        area = str(row.get("Area") or row.get("area") or "")
        year = str(row.get("Year") or row.get("year") or "")
        element = str(row.get("Element") or row.get("element") or "Value")
        unit = str(row.get("Unit") or row.get("unit") or "")
        el = element.lower()
        if "price" in el or "pp" in el:
            kind = "price"
            sections = ("prices", "world")
        elif "yield" in el:
            kind = "yield"
            sections = ("harvest", "ukraine" if "ukr" in area.lower() else "world")
        elif "area" in el or "harvested" in el:
            kind = "area"
            sections = ("harvest", "ukraine" if "ukr" in area.lower() else "world")
        elif "export" in el or "import" in el or "trade" in el:
            kind = "trade"
            sections = ("trade", "ukraine" if "ukr" in area.lower() else "world")
        else:
            kind = "production"
            sections = ("harvest", "ukraine" if "ukr" in area.lower() else "world")
        observed = f"{year}-01-01T00:00:00+00:00" if re.fullmatch(r"\d{4}", year) else _now()
        out.append(
            numeric_observation(
                provider_id=provider_id,
                source_url=source_url,
                title=f"FAOSTAT {area} {item} {element} {number} {unit} ({year})".strip(),
                value=number,
                unit=unit,
                series_id=f"faostat-{area}-{item}-{element}",
                series_kind=kind,
                observed_at=observed,
                commodity=item,
                country="UA" if "ukr" in area.lower() else area,
                source_reference=str(row.get("Domain Code") or row.get("Item Code") or f"{item}|{year}"),
                sections=sections,
            )
        )
    return out


def parse_worldbank_indicator(text: str, provider_id: str, source_url: str) -> list[dict[str, Any]]:
    body = _load_json(text)
    rows = body[1] if isinstance(body, list) and len(body) > 1 and isinstance(body[1], list) else []
    out: list[dict[str, Any]] = []
    for row in rows[:20]:
        if not isinstance(row, dict):
            continue
        number = to_float(row.get("value"))
        if number is None:
            continue
        indicator = row.get("indicator") if isinstance(row.get("indicator"), dict) else {}
        code = str(indicator.get("id") or "")
        label = str(indicator.get("value") or code or "World Bank")
        country = str((row.get("country") or {}).get("id") or row.get("countryiso3code") or "")
        year = str(row.get("date") or "")
        if "PRD" in code or "production" in label.lower():
            kind, unit, sections = "production", "t", ("harvest", "ukraine")
        elif "YLD" in code or "yield" in label.lower():
            kind, unit, sections = "yield", "kg/ha", ("harvest", "ukraine")
        elif "LND" in code or "hectare" in label.lower() or "land" in label.lower():
            kind, unit, sections = "area", "ha", ("harvest", "ukraine")
        elif (
            "TX." in code
            or "TM." in code
            or "export" in label.lower()
            or "import" in label.lower()
            or "trade" in label.lower()
        ):
            kind, unit, sections = "trade", "USD", ("trade", "ukraine")
        else:
            kind, unit, sections = "production", "", ("world",)
        observed = f"{year}-01-01T00:00:00+00:00" if re.fullmatch(r"\d{4}", year) else _now()
        iso3 = str(row.get("countryiso3code") or "")
        if iso3 == "UKR" or country in {"UA", "UKR"}:
            country = "UA"
        out.append(
            numeric_observation(
                provider_id=provider_id,
                source_url=source_url,
                title=f"{label} {country} {number} {unit} ({year})".strip(),
                value=number,
                unit=unit,
                series_id=f"wb-{code}-{country}",
                series_kind=kind,
                observed_at=observed,
                commodity="Cereals" if "CREL" in code or "cereal" in label.lower() else "",
                country=country,
                currency="USD" if kind == "trade" else "",
                source_reference=f"{code}|{year}|{country}",
                sections=sections,
            )
        )
    return out


def parse_nbu_fx(text: str, provider_id: str, source_url: str) -> list[dict[str, Any]]:
    body = _load_json(text)
    if not isinstance(body, list):
        return []
    out: list[dict[str, Any]] = []
    for row in body:
        if not isinstance(row, dict):
            continue
        code = str(row.get("cc") or "").upper()
        if code not in {"USD", "EUR"}:
            continue
        rate = to_float(row.get("rate"))
        if rate is None:
            continue
        exchanged = str(row.get("exchangedate") or "")
        observed = _iso_from_eu_date(exchanged) or _now()
        out.append(
            numeric_observation(
                provider_id=provider_id,
                source_url=source_url,
                title=f"NBU {code}/UAH {rate} ({exchanged or observed[:10]})",
                value=rate,
                unit="UAH",
                series_id=f"nbu-{code}-uah",
                series_kind="fx",
                observed_at=observed,
                commodity=code,
                country="UA",
                currency="UAH",
                source_reference=f"{code}|{exchanged}",
                sections=("prices", "ukraine"),
            )
        )
    return out


def parse_open_meteo(
    text: str,
    provider_id: str,
    source_url: str,
    *,
    region: str = "Kyiv",
    oblast_id: str = "kyiv",
    macro_region: str = "center",
) -> list[dict[str, Any]]:
    body = _load_json(text)
    if not isinstance(body, dict):
        return []
    daily = body.get("daily") if isinstance(body.get("daily"), dict) else {}
    times = daily.get("time") or []
    tmax = daily.get("temperature_2m_max") or []
    precip = daily.get("precipitation_sum") or []
    tmin = daily.get("temperature_2m_min") or []
    rain_prob = daily.get("precipitation_probability_max") or []
    wind_max = daily.get("wind_speed_10m_max") or []
    codes = daily.get("weather_code") or daily.get("weathercode") or []
    if not isinstance(times, list):
        return []
    out: list[dict[str, Any]] = []

    def _obs(day: Any, metric: str, value: float, unit: str, title: str, risk: str, observed: str) -> dict[str, Any]:
        return numeric_observation(
            provider_id=provider_id,
            source_url=source_url,
            title=title,
            value=value,
            unit=unit,
            series_id=f"open-meteo-{oblast_id}-{metric}",
            series_kind="weather",
            observed_at=observed,
            commodity="",
            country="UA",
            source_reference=f"{metric}|{oblast_id}|{day}",
            sections=("weather", "ukraine"),
            extra={
                "weather_risk": risk,
                "region": region,
                "oblast_id": oblast_id,
                "macro_region": macro_region,
                "metric": metric,
            },
        )

    for i, day in enumerate(times[:16]):
        temp = to_float(tmax[i] if i < len(tmax) else None)
        rain = to_float(precip[i] if i < len(precip) else None)
        observed = f"{day}T00:00:00+00:00" if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(day)) else _now()
        risk = "HIGH" if (rain is not None and rain >= 20) or (temp is not None and temp >= 35) else "NORMAL"
        if temp is not None:
            out.append(_obs(day, "tmax", temp, "°C", f"{region} Tmax {temp} °C ({day}) risk={risk}", risk, observed))
        if rain is not None:
            out.append(_obs(day, "precip", rain, "mm", f"{region} precipitation {rain} mm ({day}) risk={risk}", risk, observed))
        lo = to_float(tmin[i] if i < len(tmin) else None)
        if lo is not None:
            out.append(_obs(day, "tmin", lo, "°C", f"{region} Tmin {lo} °C ({day})", risk, observed))
        prob = to_float(rain_prob[i] if i < len(rain_prob) else None)
        if prob is not None:
            out.append(_obs(day, "precip_probability", prob, "%", f"{region} rain probability {prob}% ({day})", risk, observed))
        wind = to_float(wind_max[i] if i < len(wind_max) else None)
        if wind is not None:
            out.append(_obs(day, "wind", wind, "m/s", f"{region} wind {wind} m/s ({day})", risk, observed))
        code = to_float(codes[i] if i < len(codes) else None)
        if code is not None:
            out.append(_obs(day, "weather_code", code, "wmo", f"{region} weather code {int(code)} ({day})", risk, observed))

    current = body.get("current") if isinstance(body.get("current"), dict) else {}
    if current:
        observed = str(current.get("time") or _now())
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", observed):
            observed = f"{observed}T00:00:00+00:00"
        cur_map = [
            ("temperature_2m", "current_temp", "°C", "temperature"),
            ("relative_humidity_2m", "humidity", "%", "humidity"),
            ("precipitation", "current_precip", "mm", "precipitation"),
            ("wind_speed_10m", "current_wind", "m/s", "wind"),
            ("surface_pressure", "pressure", "hPa", "pressure"),
            ("weather_code", "current_weather_code", "wmo", "weather_code"),
            ("weathercode", "current_weather_code", "wmo", "weather_code"),
        ]
        seen: set[str] = set()
        for src_key, metric, unit, title_key in cur_map:
            if metric in seen:
                continue
            val = to_float(current.get(src_key))
            if val is None:
                continue
            seen.add(metric)
            out.append(_obs(observed[:10], metric, val, unit, f"{region} current {title_key} {val} {unit}", "NORMAL", observed))

    hourly = body.get("hourly") if isinstance(body.get("hourly"), dict) else {}
    soil_series = hourly.get("soil_temperature_0cm") or hourly.get("soil_temperature_6cm") or []
    hourly_times = hourly.get("time") or []
    if isinstance(soil_series, list) and soil_series:
        soil = to_float(soil_series[0])
        if soil is not None:
            stamp = str(hourly_times[0] if hourly_times else _now())
            out.append(_obs(stamp[:10], "soil_temp", soil, "°C", f"{region} soil temperature {soil} °C", "NORMAL", stamp))
    return out


def parse_numeric_for_spec(spec: dict[str, Any], text: str, source_url: str) -> list[dict[str, Any]]:
    pid = str(spec.get("id") or "")
    parser = str(spec.get("parser") or "")
    url = source_url or str(spec.get("url") or "")
    if parser == "ec_cereal" or "agrifood" in url or pid == "ec_agri":
        rows = parse_ec_cereal_prices(text, pid, url)
        if rows:
            return rows
    if parser == "eurostat_sdmx" or pid == "eurostat":
        rows = parse_eurostat_sdmx(text, pid, url)
        if rows:
            return rows
    if (
        parser == "fao_fpi"
        or "food_price_indices" in url.lower()
        or (text or "").upper().startswith("MONTHLY FOOD PRICE")
    ):
        rows = parse_fao_food_price_index(text, pid, url)
        if rows:
            return rows
    if parser == "faostat" or pid == "fao":
        rows = parse_faostat_data(text, pid, url)
        if rows:
            return rows
        rows = parse_fao_food_price_index(text, pid, url)
        if rows:
            return rows
    if parser == "worldbank" or pid == "world_bank" or "worldbank.org" in url:
        rows = parse_worldbank_indicator(text, pid, url)
        if rows:
            return rows
    if parser == "nbu_fx" or pid == "fx_rates" or "bank.gov.ua" in url:
        rows = parse_nbu_fx(text, pid, url)
        if rows:
            return rows
    if parser == "open_meteo" or "open-meteo.com" in url:
        rows = parse_open_meteo(text, pid, url)
        if rows:
            return rows
    return []
