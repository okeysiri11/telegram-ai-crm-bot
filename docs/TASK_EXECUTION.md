# Task Execution

**Sprint:** 30.5  
**File:** `src/web/src/ai-runtime/taskExecution.ts`  
**Engine:** `enterprise-runtime/jobManager.ts`

## Lifecycle API

| Action | Method |
|--------|--------|
| Create | `taskExecution.create` |
| Start | `taskExecution.start` |
| Pause | `taskExecution.pause` |
| Resume | `taskExecution.resume` |
| Cancel | `taskExecution.cancel` |
| Retry | `taskExecution.retry` |
| History | `taskExecution.history` |
| Logs | `taskExecution.logs` |
| Priority | `taskExecution.setPriority` |
| Force stop | `taskExecution.forceStop` (Owner) |

Every mutation appends logs/history and writes Audit Vault (`ai_task.*`).

## Security

Role permissions (`ai_agents`) · workspace isolation · organization isolation · audit logging — see `aiTaskSecurity.ts`.
