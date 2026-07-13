# VIN Engine v1 — validation and offline decoding (ISO 3779).

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

_VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")

_TRANSLITERATION: dict[str, int] = {
    "A": 1,
    "B": 2,
    "C": 3,
    "D": 4,
    "E": 5,
    "F": 6,
    "G": 7,
    "H": 8,
    "J": 1,
    "K": 2,
    "L": 3,
    "M": 4,
    "N": 5,
    "P": 7,
    "R": 9,
    "S": 2,
    "T": 3,
    "U": 4,
    "V": 5,
    "W": 6,
    "X": 7,
    "Y": 8,
    "Z": 9,
}

_WEIGHTS = (8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2)

_YEAR_CODES: dict[str, list[int]] = {
    "A": [1980, 2010],
    "B": [1981, 2011],
    "C": [1982, 2012],
    "D": [1983, 2013],
    "E": [1984, 2014],
    "F": [1985, 2015],
    "G": [1986, 2016],
    "H": [1987, 2017],
    "J": [1988, 2018],
    "K": [1989, 2019],
    "L": [1990, 2020],
    "M": [1991, 2021],
    "N": [1992, 2022],
    "P": [1993, 2023],
    "R": [1994, 2024],
    "S": [1995, 2025],
    "T": [1996, 2026],
    "V": [1997, 2027],
    "W": [1998, 2028],
    "X": [1999, 2029],
    "Y": [2000, 2030],
    "1": [2001, 2031],
    "2": [2002, 2032],
    "3": [2003, 2033],
    "4": [2004, 2034],
    "5": [2005, 2035],
    "6": [2006, 2036],
    "7": [2007, 2037],
    "8": [2008, 2038],
    "9": [2009, 2039],
}

_WMI_REGIONS: dict[str, str] = {
    "1": "United States",
    "2": "Canada",
    "3": "Mexico",
    "4": "United States",
    "5": "United States",
    "J": "Japan",
    "K": "South Korea",
    "L": "China",
    "S": "United Kingdom",
    "V": "France / Spain",
    "W": "Germany",
    "Y": "Sweden / Finland",
    "Z": "Italy",
}


def normalize_vin(vin: str) -> str:
    return vin.strip().upper().replace(" ", "")


def _char_value(char: str) -> int | None:
    if char.isdigit():
        return int(char)
    return _TRANSLITERATION.get(char)


def _compute_check_digit(vin: str) -> str:
    total = 0
    for idx, char in enumerate(vin):
        value = _char_value(char)
        if value is None:
            return "?"
        total += value * _WEIGHTS[idx]
    remainder = total % 11
    return "X" if remainder == 10 else str(remainder)


def _resolve_model_year(code: str) -> int | None:
    candidates = _YEAR_CODES.get(code)
    if not candidates:
        return None
    current_year = datetime.now(timezone.utc).year
    for year in reversed(candidates):
        if year <= current_year + 1:
            return year
    return candidates[-1]


def validate_vin(vin: str) -> dict[str, Any]:
    """Validate a VIN and return structured result."""
    normalized = normalize_vin(vin)
    errors: list[str] = []

    if not normalized:
        errors.append("VIN is empty")
    elif len(normalized) != 17:
        errors.append("VIN must be exactly 17 characters")
    elif not _VIN_PATTERN.match(normalized):
        errors.append("VIN contains invalid characters (I, O, Q not allowed)")
    else:
        expected = _compute_check_digit(normalized)
        actual = normalized[8]
        if expected != "?" and actual != expected:
            errors.append(f"Invalid check digit: expected {expected}, got {actual}")

    return {
        "vin": normalized,
        "is_valid": not errors,
        "errors": errors,
    }


def decode_vin(vin: str) -> dict[str, Any]:
    """Decode WMI, model year, and structural segments from a VIN."""
    validation = validate_vin(vin)
    normalized = validation["vin"]
    if not normalized or len(normalized) != 17:
        return {
            **validation,
            "decoded": None,
        }

    wmi = normalized[:3]
    vds = normalized[3:9]
    vis = normalized[9:]
    year_code = normalized[9]
    plant_code = normalized[10]
    serial_number = normalized[11:]

    region_key = wmi[0]
    region = _WMI_REGIONS.get(region_key, "Unknown")
    model_year = _resolve_model_year(year_code)

    decoded = {
        "wmi": wmi,
        "vds": vds,
        "vis": vis,
        "check_digit": normalized[8],
        "model_year_code": year_code,
        "model_year": model_year,
        "plant_code": plant_code,
        "serial_number": serial_number,
        "region": region,
        "manufacturer_hint": wmi,
    }

    return {
        **validation,
        "decoded": decoded,
    }


def build_history_event(
    event_type: str,
    *,
    source: str | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "event_type": event_type,
        "source": source,
        "description": description,
        "metadata": metadata or {},
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


def build_auction_reference(
    auction_name: str,
    *,
    lot_number: str | None = None,
    sale_date: str | None = None,
    sale_price: str | None = None,
    url: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "auction_name": auction_name,
        "lot_number": lot_number,
        "sale_date": sale_date,
        "sale_price": sale_price,
        "url": url,
        "metadata": metadata or {},
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
