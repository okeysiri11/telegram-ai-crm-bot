# AI Security — Sprint 37.2

**Extends:** APH `prompt_firewall`, `AiSecurityCenter` (32.4), client `aiPromptSecurity.ts`  
**No parallel firewall.**

## Controls

| Control | Location | 37.2 change |
|---------|----------|-------------|
| Prompt injection detection | `prompt_firewall.detect_unsafe` | Wired into **AI Runtime** `execute()` |
| Sanitization | null/bidi/script strip | Applied before complete |
| Abuse burst window | per-actor 40/min | Shared APH heuristics |
| Output leak heuristics | `AiSecurityCenter.validate_output` | Unchanged |
| Model policy | allowlist | Unchanged |
| Agent sandbox / approval | `authorize_agent_execution` | Unchanged |
| Skill signature | HMAC verify | Bypass `or True` **removed** |
| Skill elevated perms | `SkillPermissions` | Require `plugin_id` |
| Skills signing secret | `SKILLS_SIGNING_SECRET` | Env preferred |

## AI Runtime flow (hardened)

```
request → build AIRequest → AiSecurityCenter.guard_prompt
         → block | sanitize → ai_service.complete → tools → audit log
```

Blocked responses return `{ success: false, error: "prompt_blocked", reasons: [...] }` without calling the provider.

## Agent / multi-agent / memory

| Boundary | Status | Residual |
|----------|--------|----------|
| Agent permission policies | PASS (Security Center) | Deepen tool ACL P1 |
| Multi-agent session isolation | PASS (session_id contexts) | Cross-agent memory reads P1 |
| Context isolation | PASS | — |
| Memory access permissions | PASS* | Enforce tenant on all memory APIs P1 |
| Workflow permissions | PASS | — |

## Tests

- `tests/test_security_hardening_37_2.py` (runtime block/allow, skill sig)
- `tests/test_prompt_firewall_30_9.py`
- `tests/test_sprint_32_4_security_center.py`

## Verdict

**AI Runtime security verification: PASS.** Prompt injection protection enforced on the canonical runtime path.
