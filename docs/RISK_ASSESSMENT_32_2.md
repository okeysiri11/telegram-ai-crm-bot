# Risk Assessment — Sprint 32.2

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Invite URL leak | Medium | Medium | One-time token; short TTL; do not log tokens |
| Partial health probe failures | Medium | Low | Execute phase marks partial; workflows still runnable |
| Feedback without email channel | High | Low | Pilot Dashboard form + local backlog |
| Operator confusion across 7 ecosystems | Medium | Medium | `/pilot/execute` + ops guide |

Overall residual risk: **acceptable for controlled external pilot**.
