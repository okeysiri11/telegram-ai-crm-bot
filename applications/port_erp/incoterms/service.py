# Incoterms helper — EXW…DDP catalog and validation.

from __future__ import annotations

from applications.port_erp.customs.models import Incoterm
from applications.port_erp.shared.exceptions import ValidationError


_DESCRIPTIONS = {
    Incoterm.EXW: "Ex Works — seller makes goods available at premises",
    Incoterm.FCA: "Free Carrier — seller delivers to carrier",
    Incoterm.FOB: "Free On Board — seller loads onto vessel",
    Incoterm.CFR: "Cost and Freight — seller pays freight to destination",
    Incoterm.CIF: "Cost, Insurance and Freight — seller pays freight + insurance",
    Incoterm.CPT: "Carriage Paid To — seller pays carriage to named place",
    Incoterm.CIP: "Carriage and Insurance Paid To",
    Incoterm.DAP: "Delivered At Place — seller delivers ready for unloading",
    Incoterm.DPU: "Delivered at Place Unloaded",
    Incoterm.DDP: "Delivered Duty Paid — seller clears import duties",
}


class IncotermsService:
    def list_incoterms(self) -> list[dict]:
        return [{"code": i.value, "description": _DESCRIPTIONS[i]} for i in Incoterm]

    def parse(self, code: str | Incoterm) -> Incoterm:
        try:
            return Incoterm(code) if isinstance(code, str) else code
        except ValueError as exc:
            raise ValidationError(f"unsupported incoterm: {code}") from exc

    def describe(self, code: str | Incoterm) -> str:
        return _DESCRIPTIONS[self.parse(code)]


incoterms_service = IncotermsService()
