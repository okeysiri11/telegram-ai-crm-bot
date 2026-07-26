# Trade Workflow Guide — Sprint 31.1

## Flow

1. **Farm CRM** — register farmer, farm, field, supplier  
2. **Products** — list commodity product  
3. **Harvest** — season + harvest record + certificate  
4. **Warehouse** — silo + inventory incoming + elevator register  
5. **Commodity sale** — CRM buyer → marketplace offer/request/match → order  
6. **Contract** — supply-chain export contract (FOB) + docs pack + negotiation  
7. **Shipment** — sea carrier, shipment, BL/docs, container, dispatch, customs, tracking  
8. **Platform** — notification → AI Team → Concierge → AMO → owner dashboard → MC → analytics → quality gates → OBS  

## Notes

- Prefer SC `POST …/export {action:"contract"}` over orphan trading contracts without marketplace orders.  
- Pricing remains on agro marketplace/pricing surfaces (not ECO retail payments).  
- Beauty/Cafe continue to use Commerce Core; Agriculture uses grain marketplace trade.

## UI entry

`/workspace/agro` → **Execute Agriculture pilot**
