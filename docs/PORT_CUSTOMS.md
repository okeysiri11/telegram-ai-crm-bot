# Port ERP Customs & International Trade — Sprint 9.4

Customs, documentation, and international cargo flow for **Port ERP 1.3.0-alpha**.

| Field | Value |
|-------|-------|
| Application version | `1.3.0-alpha` |
| Customs engine | `1.0` |
| Platform | AI Platform Core v3 (bridge only) |
| Ecosystem | AI Ecosystem v1.5 (bridge only) |

**Hard constraint:** Platform Core and Ecosystem are not modified. Everything lives under `applications/port_erp/`.

## Engines

| Engine | Module |
|--------|--------|
| Customs Engine | `customs/engine.py` |
| Cargo Documentation Engine | `documents/engine.py` |
| International Trade Engine | `international_trade/engine.py` |
| Broker Operations Engine | `broker/engine.py` |
| Inspection Engine | `inspection/engine.py` |
| Compliance Engine | `compliance/engine.py` |
| Certificate Manager | `certificates/engine.py` |
| Tariff Engine | `tariffs/engine.py` |
| Cargo Flow Engine | `cargo_flow/engine.py` |
| Incoterms Service | `incoterms/service.py` |

## Supported documents

Bill of Lading · Sea Waybill · CMR · Rail Waybill · Air Waybill · Commercial Invoice · Packing List · Certificate of Origin · Phytosanitary · Veterinary · Quality · Insurance · Export / Import / Transit Declaration · Dangerous Goods Declaration

## Customs workflow

Export · Import · Transit · Temporary Storage · Customs Inspection · Release · Hold · Risk Assessment · Random Inspection · Green / Yellow / Red channel

## Incoterms

`EXW` · `FCA` · `FOB` · `CFR` · `CIF` · `CPT` · `CIP` · `DAP` · `DPU` · `DDP`

## Cargo flow

`booking` → `documentation` → `customs_clearance` → `loading` → `departure` → `transit` → `arrival` → `discharge` → `warehouse` → `delivery` → `completed`

## Events

`CustomsDeclarationCreated` · `CustomsReleased` · `CustomsInspectionStarted` · `CargoHeld` · `CargoReleased` · `CertificateIssued` · `DocumentSigned` · `ExportCompleted` · `ImportCompleted`

## REST API

| Area | Prefix |
|------|--------|
| Customs | `/api/port/v1/customs` |
| Documents | `/api/port/v1/documents` |
| Certificates | `/api/port/v1/certificates` |
| Trade | `/api/port/v1/trade` |
| Broker | `/api/port/v1/broker` |
| Compliance | `/api/port/v1/compliance` |

## Developer guide

```python
from applications.port_erp import port_erp
from applications.port_erp.customs.models import TradeShipment, DocumentType, TradeDocument

shipment = port_erp.customs.trade.create_shipment(
    TradeShipment(cargo_id="c1", seller="ExCo", buyer="ImCo", incoterm="FOB", declared_value=50000)
)
port_erp.customs.documents.create(
    TradeDocument(document_type=DocumentType.BILL_OF_LADING, shipment_id=shipment.shipment_id, title="B/L")
)
decl = await port_erp.customs.trade.start_customs(shipment.shipment_id, procedure="export", hs_code="100590")
```

## Related

- [PORT_ERP.md](PORT_ERP.md)
- [PORT_TRACKING.md](PORT_TRACKING.md)
- [PORT_TERMINAL.md](PORT_TERMINAL.md)
