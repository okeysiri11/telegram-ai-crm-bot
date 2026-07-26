# Beauty Workflow — Sprint 30.9

```
Customer → Login → Choose Service → Choose Specialist → Calendar → Booking
  → Confirmation → Reminder → Visit → CRM Update → Analytics → Mission Control
```

Supporting: Rooms/Resources · Working Hours · Payment · AI Team · Concierge · AMO · Quality Gates · OBS

## Step → API

| Step | API |
|------|-----|
| Login | ISAM `/health` + session gate |
| Salon CRM | `POST …/bos/v1/bootstrap` |
| Working hours | `POST …/bos/v1/branches` (+ schedule) |
| Rooms/resources | `GET/POST …/bos/v1/resources` |
| Customer | `POST …/bos/v1/customers` |
| Choose service | `POST …/bos/v1/services` |
| Choose specialist | `POST …/bos/v1/employees` |
| Calendar | `POST …/bcj/v1/availability` + `GET …/bws/v1/schedule` |
| Booking | `POST …/bcj/v1/book` |
| Confirmation | `POST …/bos/v1/appointments` status=confirmed |
| Reminder | `POST …/comms/v1/center` |
| AI reminder / receptionist | BCJ `/assistant` + BWS `/assistant` |
| Payment | `POST …/eco/v1/payments` |
| Visit | appointment status=completed |
| CRM update | BCJ `/journey` + `/loyalty` |
| AI Team | PB `/ai-team/*` assign_task |
| AI Concierge | PB `/concierge/*` |
| AI Marketing | AMO bootstrap/campaigns/performance |
| Owner dashboard | BOS + BWS `/dashboard` |
| Analytics | BOS/BWS dashboards |
| Mission Control | PB `/mission-control/*` |
| Quality gates | BOS/BWS/BCJ/ECO/ISAM/OBS/MC/EWF health |
| Observability | OBS logs + metrics |
