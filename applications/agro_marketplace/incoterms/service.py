# Incoterms catalog — FOB, CIF, CFR, DAP, EXW, DDP.

from __future__ import annotations

from applications.agro_marketplace.export.models import Incoterm, IncotermCode

_INCOTERMS: dict[IncotermCode, Incoterm] = {
    IncotermCode.EXW: Incoterm(
        code=IncotermCode.EXW,
        name="Ex Works",
        description="Buyer collects goods at seller premises",
        seller_responsibility="make_goods_available",
        buyer_responsibility="all_transport_and_risk",
    ),
    IncotermCode.FOB: Incoterm(
        code=IncotermCode.FOB,
        name="Free On Board",
        description="Seller delivers goods on board vessel at origin port",
        seller_responsibility="load_on_vessel",
        buyer_responsibility="main_carriage_and_insurance",
    ),
    IncotermCode.CFR: Incoterm(
        code=IncotermCode.CFR,
        name="Cost and Freight",
        description="Seller pays freight to destination port",
        seller_responsibility="freight_to_destination",
        buyer_responsibility="insurance_and_import",
    ),
    IncotermCode.CIF: Incoterm(
        code=IncotermCode.CIF,
        name="Cost Insurance and Freight",
        description="Seller pays freight and insurance to destination port",
        seller_responsibility="freight_and_insurance",
        buyer_responsibility="import_clearance",
    ),
    IncotermCode.DAP: Incoterm(
        code=IncotermCode.DAP,
        name="Delivered At Place",
        description="Seller delivers to named place ready for unloading",
        seller_responsibility="deliver_to_place",
        buyer_responsibility="unload_and_import",
    ),
    IncotermCode.DDP: Incoterm(
        code=IncotermCode.DDP,
        name="Delivered Duty Paid",
        description="Seller delivers cleared for import at destination",
        seller_responsibility="all_costs_including_duties",
        buyer_responsibility="unload",
    ),
}


class IncotermsService:
    def list_incoterms(self) -> list[Incoterm]:
        return list(_INCOTERMS.values())

    def get(self, code: IncotermCode | str) -> Incoterm:
        key = IncotermCode(code) if isinstance(code, str) else code
        return _INCOTERMS[key]

    def supports(self, code: str) -> bool:
        return code.upper() in IncotermCode._value2member_map_


incoterms_service = IncotermsService()
