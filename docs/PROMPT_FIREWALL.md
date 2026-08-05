# Prompt Firewall

**Sprint:** 32.4 (documents) · **Implementation:** Sprint 30.9  
**Canonical code:** `applications/enterprise_hub/ai_provider_hub/prompt_firewall.py`  
**Facade:** `platform_security.ai_security_center.AiSecurityCenter.guard_prompt`  
**Web mirror:** `src/web/src/ai-runtime/aiPromptSecurity.ts`

## Controls

| Control | Behavior |
|---|---|
| Sanitize | Strip nulls, bidi overrides, script tags |
| Injection / jailbreak detection | Deny-list regex patterns |
| Abuse detection | Per-actor burst window |
| Token policy | Estimate + truncate to max_tokens |
| Output validation | Leak heuristics via AI Security Center |

Do **not** invent a second prompt firewall product. Extend APH + facade.
