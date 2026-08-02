# UX Migration Plan — Sprint 33.1

1. **Ship mode store + toggle** — default Simple; Pro restores prior IA.
2. **Filter Sidebar + palette** — no route deletions.
3. **Context nav** — activate on module routes; “← Все модули” returns home.
4. **Role workspaces** — first-entry personas + top-nav selector.
5. **Executive dashboard** — Simple `/dashboard` default; `?mode=full` for legacy Command Center.
6. **AI intents** — deterministic map in Ctrl+K; Pro auto-switch for Pro-only targets.
7. **Docs + tests** — `uxRevolution.test.ts`; bump `webConfig.sprint` to `33.1`.

## Rollback

Set `localStorage.ewp_ux_mode_v1 = "pro"` or toggle Pro in the header to restore full navigation without redeploy.
