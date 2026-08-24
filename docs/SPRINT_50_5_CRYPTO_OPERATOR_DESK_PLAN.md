# Sprint 50.5 — Operator Desk Hardening (Plan)

## Goal

Configurable timezone-aware analysis schedules, working specialist settings, complete signal create flow, Risk Agent R/R warnings for paper, durable persistence/idempotency, honest DXY TV fallback, green chart CTAs. No real broker. No Sprint 50.6.

## Architecture (extend, do not replace)

| Area | Extension point |
|------|-----------------|
| Schedule | `services/fx_market_intel/schedule.py` + POST upsert; prefs timezone |
| Specialists | Expand `otcPrefs` AgentSettingsMap; pass weights into consensus |
| Signals | `kind` + form fields in payload; sound profiles |
| Paper risk | `risk_preview` R/R + Risk Agent soft warning |
| Persistence | Additive migration `a0u123456789_fx_desk_50_5` |
| UI | Crypto desk panels only |

## Defaults (configurable, not hardcoded business logic)

| Preset | Default local time | Default TZ |
|--------|-------------------|------------|
| Morning | 07:00 | Europe/Kyiv (user-overridable) |
| Before Europe | 07:30 | Europe/Kyiv |
| Before USA | 15:00 | Europe/Kyiv |
| Evening | 20:00 | Europe/Kyiv |
