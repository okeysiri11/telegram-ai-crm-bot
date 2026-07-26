# Logistics Guide — Sprint 31.1

## Validated surfaces

| Capability | API |
|------------|-----|
| Sea freight | Agro carriers `mode:"sea"` + logistics plan |
| Container tracking | `/logistics/containers` + `/tracking/{shipment_id}` |
| Warehouse logistics | Agro warehouses + SC elevator |
| Transport / freight plan | SC `/logistics` `action:"freight"` / `route` / `delivery` |
| Bills of Lading / docs | Export shipment documents + SC export `action:"docs"` |
| Certificates | Harvest certificates |
| Customs | `/export/shipments/{id}/customs` |
| Delivery status | Tracking + SC delivery window |

## Quality gates

Probes agro, supply-chain, ISAM, OBS, Mission Control, EWF, plus Auto/Beauty/Cafe health for cross-ecosystem regression.
