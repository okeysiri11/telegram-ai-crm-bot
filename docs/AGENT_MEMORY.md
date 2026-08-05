# Agent Memory

**Sprint:** 32.1 · `agentOs.remember` / `recall` / `sharedContext`

## Kinds

| Kind | Use |
|---|---|
| short | Per-task scratch |
| long | Durable agent notes |
| vector | Placeholder key for embeddings (APH later) |
| knowledge | Knowledge refs |
| company | Tenant / brand knowledge |
| user | User preferences |
| session | Current session context |

Tenant isolation via `tenantId` on every entry. Secrets never stored in memory values — use ESH vault refs.
