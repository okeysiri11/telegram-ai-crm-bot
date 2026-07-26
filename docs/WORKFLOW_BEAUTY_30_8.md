# Beauty Workflow Documentation — Sprint 30.8

## Flow

```
Client → Authentication → Appointment → Calendar → AI Reminder → CRM Update
  → Owner Dashboard → Mission Control → Analytics
```

(Plus shared Concierge, Notification, Quality Gates, OBS — same template as Automotive.)

## Step map

| Step | API / surface |
|------|----------------|
| Staff auth | ProtectedRoute + validateSession (ISAM/JWT) |
| Salon CRM bootstrap | `POST /api/enterprise-bos/v1/bootstrap` |
| Client | `POST /api/enterprise-bos/v1/customers` |
| Services + employees | `POST …/services`, `POST …/employees` |
| Appointment | `POST /api/enterprise-bcj/v1/book` (fallback BOS appointments) |
| Calendar | `GET/POST /api/enterprise-bws/v1/schedule` |
| AI reminder | `POST /api/enterprise-bcj/v1/assistant` + BWS notifications |
| CRM update | `POST /api/enterprise-bcj/v1/journey` |
| AI Concierge | PB `/concierge/sessions` (shared) |
| Marketing | AMO `/health` + `/bootstrap` |
| Owner dashboard | BOS + BWS `/dashboard` |
| Mission Control | PB `/mission-control/status` + `/activity` |
| Analytics | BOS/BWS dashboards |
| Notification | enterprise-comms `/center` |
| Quality gates | BOS/BWS/BCJ/OBS health |
| Observability | OBS `/logs` + `/metrics` |

## Execute

1. Login at `/login` with production credentials  
2. Open `/workspace/beauty`  
3. Enter client name/email  
4. **Execute Beauty workflow**  
5. Confirm all steps ok in the execution log  
6. Review `/pilot` metrics and Mission Control  

## Observability collected

Appointments · Workflow completion · Customer sessions · AI actions · Business events · Errors · Performance (via pilotMetrics + OBS)
