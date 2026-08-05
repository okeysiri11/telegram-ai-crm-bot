# Automation Center

**Sprint:** 28.9  
**Route:** `/automation` (alias `/automation-center`)  
**Page:** `src/web/src/runtime/automation/AutomationCenterPage.tsx`

## Tabs / panels

1. **Inspector** — registered automations, enable state, run / pause / resume  
2. **Queue** — live jobs by status, cancel / retry  
3. **History** — persisted outcomes + success/failure rates  
4. **Timeline** — flattened execution events across jobs  

## Monitoring metrics

- Live queue counts (pending · running · waiting · retry · …)
- Retry statistics (from history attempts)
- Average duration
- Success rate / failure rate

## Navigation

- Desktop tools group · Shell quick action `qa_automation`
- Command `auto_open_center`
- Workflow Runtime inspector link
- AI Builder Studio strip
