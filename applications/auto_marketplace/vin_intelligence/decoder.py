"""VIN Decoder & manufacturer intelligence — Sprint 13.1."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

# Minimal WMI → manufacturer map for deterministic decoding
_WMI_MANUFACTURERS: dict[str, dict[str, str]] = {
    "WVW": {"manufacturer": "Volkswagen", "country": "Germany", "region": "EU"},
    "WBA": {"manufacturer": "BMW", "country": "Germany", "region": "EU"},
    "WDB": {"manufacturer": "Mercedes-Benz", "country": "Germany", "region": "EU"},
    "1HG": {"manufacturer": "Honda", "country": "USA", "region": "NA"},
    "1FT": {"manufacturer": "Ford", "country": "USA", "region": "NA"},
    "5YJ": {"manufacturer": "Tesla", "country": "USA", "region": "NA"},
    "JN1": {"manufacturer": "Nissan", "country": "Japan", "region": "APAC"},
    "JTD": {"manufacturer": "Toyota", "country": "Japan", "region": "APAC"},
    "VF1": {"manufacturer": "Renault", "country": "France", "region": "EU"},
    "ZFA": {"manufacturer": "Fiat", "country": "Italy", "region": "EU"},
}

_YEAR_CODES = {
    "A": 2010, "B": 2011, "C": 2012, "D": 2013, "E": 2014, "F": 2015,
    "G": 2016, "H": 2017, "J": 2018, "K": 2019, "L": 2020, "M": 2021,
    "N": 2022, "P": 2023, "R": 2024, "S": 2025, "T": 2026,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _normalize_vin(vin: str) -> str:
    return (vin or "").strip().upper().replace(" ", "")


class VINDecoder:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def validate_format(self, vin: str) -> dict[str, Any]:
        vin = _normalize_vin(vin)
        issues: list[str] = []
        if len(vin) != 17:
            issues.append("length_not_17")
        if any(c in vin for c in "IOQ"):
            issues.append("illegal_chars_ioq")
        if not vin.isalnum() and vin:
            issues.append("non_alphanumeric")
        return {
            "vin": vin,
            "valid_format": len(issues) == 0 and len(vin) == 17,
            "issues": issues,
        }

    def decode(self, vin: str) -> dict[str, Any]:
        check = self.validate_format(vin)
        vin = check["vin"]
        if len(vin) < 11:
            raise ValidationError("VIN must be at least 11 characters")
        wmi = vin[:3]
        vds = vin[3:9] if len(vin) >= 9 else vin[3:]
        vis = vin[9:] if len(vin) >= 10 else ""
        mfr = _WMI_MANUFACTURERS.get(wmi, {"manufacturer": "Unknown", "country": "Unknown", "region": "Unknown"})
        year_code = vin[9] if len(vin) > 9 else ""
        plant_code = vin[10] if len(vin) > 10 else ""
        serial = vin[11:] if len(vin) > 11 else ""
        decoded = {
            "decode_id": _id("videc"),
            "vin": vin,
            "wmi": wmi,
            "vds": vds,
            "vis": vis,
            "manufacturer": mfr["manufacturer"],
            "country": mfr["country"],
            "market_region": mfr["region"],
            "production_plant": f"Plant-{plant_code or 'X'}",
            "production_date": {"model_year": _YEAR_CODES.get(year_code), "year_code": year_code},
            "factory_configuration": {"vds": vds, "options_hash": vds[:4] if vds else ""},
            "engine": self._engine_decode(vds, manufacturer=mfr["manufacturer"]),
            "transmission": self._transmission_decode(vds),
            "trim": self._trim_decode(vds),
            "package": self._package_decode(vds),
            "serial": serial,
            "format_check": check,
            "decoded_at": _now(),
        }
        return self.store.vi_decodes.save(decoded["decode_id"], decoded)

    def _engine_decode(self, vds: str, *, manufacturer: str = "") -> dict[str, Any]:
        code = (vds[0:2] if len(vds) >= 2 else "XX")
        fuel = "electric" if manufacturer == "Tesla" or "E" in code else "gasoline"
        return {"code": code, "family": f"ENG-{code}", "fuel": fuel}

    def _transmission_decode(self, vds: str) -> dict[str, Any]:
        code = vds[2] if len(vds) >= 3 else "X"
        return {"code": code, "type": "automatic" if code in "ABCDEF" else "manual"}

    def _trim_decode(self, vds: str) -> dict[str, Any]:
        code = vds[3] if len(vds) >= 4 else "B"
        levels = {"A": "base", "B": "comfort", "C": "sport", "D": "luxury", "E": "premium"}
        return {"code": code, "level": levels.get(code, "standard")}

    def _package_decode(self, vds: str) -> dict[str, Any]:
        code = vds[4:6] if len(vds) >= 6 else "00"
        return {"code": code, "packages": ["tech"] if code.endswith("1") else ["standard"]}

    def manufacturer_lookup(self, wmi: str) -> dict[str, Any]:
        wmi = (wmi or "").upper()[:3]
        info = _WMI_MANUFACTURERS.get(wmi)
        if not info:
            raise ValidationError(f"unknown WMI: {wmi}")
        return {"wmi": wmi, **info}

    def status(self) -> dict[str, Any]:
        return {
            "decodes": self.store.vi_decodes.count(),
            "known_wmi": len(_WMI_MANUFACTURERS),
        }
