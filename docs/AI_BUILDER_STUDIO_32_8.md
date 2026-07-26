# AI Builder Studio — Sprint 32.8

Platform Builder **v1.54.0** · Sprint **32.8**

## Goal

Единый конструктор платформы: пользователь собирает AI Team, Workflow, Skills, Prompts и Templates — без новых Builder / Workflow Engine / AI Core.

## Constraints

- **No new Builder Engine**
- **No new Workflow Engine**
- **No new AI Core**
- Reuse: AI Builder wizard + catalogs, AI Team API, Workflow Automation templates, Enterprise Intelligence / live-ops, Knowledge, Mission Control, seven ecosystems

## Delivered

1. **Builder Home** — карточки AI Team / Workflow / Knowledge / Integrations / Skills / Prompts / Templates  
2. **AI Team Builder** — визуальный редактор (роль, навыки, приоритет, доступ) поверх `…/ai-team/…/actions`  
3. **Workflow Builder** — визуализация существующих шаблонов  
4. **Skill Library** — CRM · Marketing · Sales · Legal · Analytics · Finance · Knowledge · Automation  
5. **Prompt Library** — system / user / corporate / favorite  
6. **Template Library** — Beauty · Legal · Cafe · Automotive · Agriculture · Drone · Bidex  
7. **Builder Dashboard** — counts AI / Workflow / Skills / Prompts / Templates  

## Routes

- `/platform-builder/builder-studio` — Studio  
- `/platform-builder/ai` — same Studio (wizard via `?section=wizard`)  
