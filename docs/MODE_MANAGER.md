# Mode Manager

**Epic:** 45.1 · **Version:** 45.1.0  
**Package:** `platform_modes/`

## Modules

| File | Role |
|------|------|
| `mode_state.py` | `WorkMode` enum + RU indicators |
| `session_mode.py` | Per-owner session + defaults |
| `mode_switch.py` | NL / button command matching |
| `permissions.py` | Settings + confirmation policy |
| `manager.py` | Façade + AI Command Center gate |

## Enum

- `HUMAN_MODE` · `AI_MODE` · `VOICE_MODE` · `AUTO_MODE` (disabled)

Only one active mode at a time.

## API

| Method | Path |
|--------|------|
| GET | `/api/v1/mode` |
| GET | `/api/v1/mode/status` |
| POST | `/api/v1/mode/change` |
| POST | `/api/v1/mode/voice` |
| POST | `/api/v1/mode/settings` |
| POST | `/api/v1/mode/remember` |

## Integration

`ModeManager.run_command_if_allowed` → `ai_command_center.handle` → Hercules.

## Channels

- **Web** — Header `ModeSwitch` + `/settings/ai-mode`
- **Desktop** — menubar near profile status
- **Telegram** — `⚙ Режим работы`
