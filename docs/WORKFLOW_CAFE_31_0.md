# Cafe Workflow — Sprint 31.0

```
Customer → Login → View Menu → Reserve Table → Place Order → Kitchen Queue
  → Payment → Loyalty → CRM → Mission Control → Analytics
```

Plus: Staff · QR Menu · Delivery · AI Team · Concierge · AMO · Notifications · Quality Gates · OBS

## Step → API

| Step | API |
|------|-----|
| Login | ISAM health + session |
| Restaurant CRM | `POST …/cos/v1/bootstrap` |
| View menu | `GET …/cos/v1/menu` |
| QR menu | `POST …/cos/v1/qr-menu` |
| Tables | `GET …/cos/v1/tables` |
| Reserve | `POST …/cos/v1/reservations` |
| Order | `POST …/cos/v1/orders` |
| Kitchen | `GET/POST …/cos/v1/kitchen` |
| Payment | `POST …/eco/v1/payments` |
| Loyalty | `POST …/eco/v1/loyalty` |
| CRM | `POST …/cos/v1/crm` |
| AI Team / Concierge | PB `/ai-team/*`, `/concierge/*` |
| Mission Control | PB `/mission-control/*` |
| Analytics | `GET …/cos/v1/dashboard` |
