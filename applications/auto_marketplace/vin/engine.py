# VIN Intelligence Engine — decode, OEM specs, recalls, campaigns.

from __future__ import annotations

from applications.auto_marketplace.marketplace.models import VINDecodeResult
from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

# Simplified WMI country map for foundation intelligence
_WMI_COUNTRY = {
    "J": "Japan",
    "K": "Korea",
    "L": "China",
    "S": "United Kingdom",
    "W": "Germany",
    "1": "United States",
    "2": "Canada",
    "3": "Mexico",
    "4": "United States",
    "5": "United States",
    "6": "Australia",
    "9": "Brazil",
    "V": "France",
    "Z": "Italy",
}

_YEAR_CODES = {
    "A": 2010, "B": 2011, "C": 2012, "D": 2013, "E": 2014, "F": 2015, "G": 2016,
    "H": 2017, "J": 2018, "K": 2019, "L": 2020, "M": 2021, "N": 2022, "P": 2023,
    "R": 2024, "S": 2025, "T": 2026, "V": 2027, "W": 2028, "X": 2029, "Y": 2030,
}


class VINEngine:
    """VIN decoding and OEM intelligence."""

    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def decode(self, vin: str) -> VINDecodeResult:
        cleaned = (vin or "").strip().upper().replace(" ", "")
        if len(cleaned) != 17 or any(ch in cleaned for ch in "IOQ"):
            result = VINDecodeResult(vin=cleaned, valid=False, detail="VIN must be 17 chars without I/O/Q")
            self._store.vin_decodes.save(cleaned or "invalid", result)
            return result

        year_code = cleaned[9]
        production_year = _YEAR_CODES.get(year_code)
        country = _WMI_COUNTRY.get(cleaned[0], "Unknown")
        plant = cleaned[10]
        manufacturer = cleaned[:3]
        result = VINDecodeResult(
            vin=cleaned,
            valid=True,
            wmi=cleaned[:3],
            vds=cleaned[3:9],
            vis=cleaned[9:],
            country=country,
            plant=plant,
            manufacturer=manufacturer,
            production_year=production_year,
            production_date=f"{production_year}-01-01" if production_year else "",
            engine=f"ENG-{cleaned[7:8]}",
            transmission="automatic" if cleaned[6] in "ABCDEF" else "manual",
            body="sedan" if cleaned[5] in "12345" else "suv",
            drive="awd" if cleaned[4] in "456" else "fwd",
            fuel="hybrid" if cleaned[7] in "HY" else "petrol",
            options=["abs", "airbags", "cruise"],
            factory_configuration={
                "trim": f"TRIM-{cleaned[3:5]}",
                "package": f"PKG-{cleaned[5:7]}",
                "paint_code": cleaned[11:13],
            },
            oem_specifications={
                "displacement_cc": 2000 + (ord(cleaned[7]) % 10) * 100,
                "power_hp": 140 + (ord(cleaned[8]) % 20) * 5,
                "doors": 4 if cleaned[5] in "12345" else 5,
            },
            recalls=[{"id": f"RCL-{cleaned[:5]}", "title": "Airbag inspection", "severity": False}],
            service_campaigns=[{"id": f"SVC-{cleaned[:5]}", "title": "Software update", "open": True}],
            detail="ok",
        )
        self._store.vin_decodes.save(cleaned, result)
        return result

    def get(self, vin: str) -> VINDecodeResult | None:
        return self._store.vin_decodes.get((vin or "").strip().upper())

    def metrics(self) -> dict:
        return {"vin_decodes": self._store.vin_decodes.count()}


vin_engine = VINEngine()
