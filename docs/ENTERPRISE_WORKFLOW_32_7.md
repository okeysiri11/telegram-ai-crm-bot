# Enterprise Workflow Automation — Sprint 32.7

Platform Builder **v1.53.0** · Sprint **32.7**

## Goal

Показать законченные бизнес-Workflow, выполняемые AI-командой — без новых Workflow / Automation Engine / AI Core / Store.

## Constraints

- **No new Workflow Engine**
- **No new Automation Engine**
- **No new AI Core**
- **No new Store**
- Reuse: AI Core, AI Team, Mission Control, Workspace Engine, Dashboard, Enterprise Intelligence, Notification Center, Knowledge Base, Business Ecosystems, Enterprise City, live-ops, Hub `TEMPLATE_KINDS`

## Delivered

1. **Workflow Center** — `/platform-builder/workflow-center` (active / completed / waiting / errors)
2. **Workflow Timeline** — step sequence for selected run
3. **Workflow Monitor** — status, duration, executor, next step, result
4. **AI Chain** — Concierge → specialists → Completed
5. **Business Templates** — library mapped to Hub kinds
6. **Executive View** — completed / automated / time saved / active / errors
7. **Enterprise City route** — SVG hops between buildings (`?wf=`)
8. **Performance** — shared `useLiveEnterprise` only

## Templates

| ID | Library label | Hub kind |
|----|---------------|----------|
| new_client | Новый клиент | crm_lead_processing |
| sale | Продажа | crm_lead_processing |
| contract | Подписание договора | contract_approval |
| project | Создание проекта | ai_task_processing |
| request | Новая заявка | customer_support |
| invoice | Согласование счёта | invoice_approval |
| onboarding | Онбординг сотрудника | employee_onboarding |
| maintenance | Обслуживание оборудования | equipment_maintenance |
