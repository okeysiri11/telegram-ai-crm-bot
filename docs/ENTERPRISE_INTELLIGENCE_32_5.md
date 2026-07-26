# Enterprise Intelligence Layer — Sprint 32.5

Platform Builder **v1.51.0** · Sprint **32.5**

## Goal

Сделать AI проактивным: система анализирует live-данные и помогает принимать решения без новых Engine / AI Core / Concierge.

## Constraints

- **No new Engine**
- **No new AI Core**
- **No new Concierge**
- Reuse: AI Core, Concierge, AI Team, Workspace Engine, Mission Control, Dashboard, Enterprise City, Knowledge Base, Context Providers, live-ops shared snapshot, Notification Center

## Delivered

### 1. Enterprise Insights

Единый блок: события дня, отклонения, риски, достижения, возможности — derive из `LiveEnterpriseSnapshot` + notifications.

### 2. Daily Brief

Краткая сводка при входе (раз в день): задачи, риски/сделки, AI-автоматизации, внимание к клиентам, Knowledge updates.

### 3. Smart Priorities

Сортировка: срочные / важные / ожидающие / рекомендуемые.

### 4. Cross-Module Intelligence

Связи CRM→Finance, Documents/Knowledge→Legal, Marketing→Sales, AI→CRM, Automation→Production по `activeModules` / activity hints.

### 5. Executive Decision Panel

Что решить сегодня · что может подождать · риски · возможности.

### 6. Knowledge Awareness

Сигналы KB/docs в health, activity и recommendations поднимают приоритеты и Concierge suggestions.

### 7. Performance

Только клиентский derive поверх shared `useLiveEnterprise` (dedupe 2.5s) — без дополнительных API.

## Architecture note

`src/web/src/enterprise-intelligence/` — presentational + pure functions. Mount: FullLayout (compact) + Dashboard (full).
