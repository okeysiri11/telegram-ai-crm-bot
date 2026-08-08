# EPIC 45.1 — Human Mode / AI Mode (Dual Experience)

**Status:** Done  
**Date:** 2026-08-07  
**Mode:** Enterprise AI OS + Human First + AI First + Hercules + Telegram First + Voice First + Russian First

## Goal

Платформа одинаково хорошо работает как классическая CRM/ERP и как AI-управляемая система.  
AI никогда не навязывается — пользователь выбирает режим.

## Shipped

### Backend — `platform_modes/`

- `WorkMode`: HUMAN / AI / VOICE / AUTO (future, disabled)
- Session restore, remember default, settings toggles
- NL commands (AI ON/OFF, VOICE, стоп, …)
- Gate: Human = explicit ask only; AI/Voice = full Command Center → Hercules
- Sensitive actions always require confirmation

### API

- `GET /api/v1/mode` · `GET /api/v1/mode/status`
- `POST /api/v1/mode/change` · `/mode/voice` · `/mode/settings` · `/mode/remember`

### Telegram

- Main menu: `⚙ Режим работы`
- Buttons: Human / AI / Voice / remember default
- NL mode commands
- AI Command path uses `run_command_if_allowed`

### Web

- Header switch: ⚪ Human · 🟢 AI · 🎙 Voice
- Mode indicator on all shells using `ModeSwitch` / `ModeIndicator`
- Page `/settings/ai-mode` («Настройки AI»)

### Desktop

- Switch + indicator next to profile/status in menubar

### Docs

- `HUMAN_MODE.md` · `AI_MODE.md` · `VOICE_MODE.md` · `MODE_MANAGER.md`

## Architectural decisions

1. **Extend, don’t fork AI stack** — modes gate `platform_ai_command`, never call agents/providers directly.
2. **AUTO_MODE reserved** — enum present, API returns error / store falls back to Human.
3. **Local-first Web store** — zustand + localStorage with best-effort API sync (offline-safe).
4. **Confirmation always for delete/pay/export/publish/ads/settings** — independent of mode.

## Tests

- `tests/test_dual_experience_45_1.py` — 250+ cases (switch, permissions, Telegram, API, gate, restore, smoke)
- Web: `src/web/src/platform-modes/modeStore.test.ts`

## Deferred

- Wake word
- AUTO_MODE scheduling
- Persistent DB-backed mode per tenant (in-memory session store for now)
