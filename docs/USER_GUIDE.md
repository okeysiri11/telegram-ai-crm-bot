# Agro Marketplace User Guide

## Who this is for

Farmers, buyers, suppliers, exporters, and logistics users of Agro Marketplace **2.0.0**.

## Getting started

1. Register via Farmer/Buyer portal: `POST /api/agro/v1/portal/users`
2. Open your portal: `GET /api/agro/v1/portal/{farmer|buyer|supplier|exporter}`
3. Mobile users: `POST /api/agro/mobile/v1/auth`

## Common tasks

| Task | Where |
|------|--------|
| List / search products | Catalog & Mobile products API |
| Create offers / RFQs | Marketplace portal widgets / CRM APIs |
| Track export shipment | Export + tracking APIs |
| Ask AI assistant | Portal or Mobile `/assistant` |
| View notifications | Notification Center / Mobile inbox |
| Share documents | Portal documents share |
| Message counterparties | Portal messaging threads |

## Portals

- **Farmer** — harvest, crops, assistant tips
- **Buyer** — demand and pricing
- **Supplier** — supply and sales
- **Exporter** — export corridors and regional views
- **Executive** — KPI dashboard and insights

## Tips

- Keep profile email unique; mobile auth reuses portal users by email
- AI alerts appear as `ai_alert` channel notifications
- Export documents (invoice, packing list, BoL, certificates) are prepared per shipment
