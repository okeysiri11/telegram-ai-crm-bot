# Voice Command Center — Sprint 36.6

## Architecture decision

**Canonical SoR:** `platform_ai` (AI modality + runtime).  
**Rejected:** new `platform_voice` / `platform_core/` package.  
**Kernel mirror:** Node `@ados/voice` (`src/voice/`) remains the client/kernel implementation; Python productizes enterprise control-plane APIs, persistence, and Web console.

```
Microphone / Push-to-talk / Wake word / Continuous + VAD
                ↓
      SpeechProviderManager (fallback chain)
   openai_realtime → whisper → deepgram → azure → google → local_whisper
                ↓
         VoiceCommandParser (NLU intents)
                ↓
         VoiceSecurity (RBAC · confirm · audit · encrypt)
                ↓
      Command Execution → AI Runtime · Workflow · Context · Event Bus · Service Builder
```

---

## Voice Runtime

| Feature | Support |
|---------|---------|
| Microphone input | Device registry + Live Microphone UI |
| Streaming STT | `streaming=true` on process |
| Push-to-talk | `VoiceMode.push_to_talk` |
| Wake word | Default `hey ados` |
| Continuous listening | `VoiceMode.continuous` |
| VAD | `POST /sessions/{id}/vad` |

## Speech Providers

OpenAI Realtime · Whisper · Azure Speech · Deepgram · Google Speech · Local Whisper — automatic fallback via `SpeechProviderManager`.

## Command Parser Intents

`open_page` · `create_project` · `create_task` · `assign_employee` · `search_knowledge` · `open_crm` · `open_erp` · `launch_workflow` · `call_ai_agent` · `generate_report`

## Security

- Role-based permissions (`owner` / `administrator` / `operator` / `readonly`)
- Confirmation for `confirm` / `dangerous` intents
- Dangerous approval (`assign_employee`)
- Audit trail in `voice_history`
- Encrypted session storage tokens (demo HMAC + integrity check)

## REST API

| Prefix | Purpose |
|--------|---------|
| `/api/voice/*` | Primary |
| `/api/voice-runtime/*` | Alias |
| `/management/v1/voice/*` | Management dual-prefix |

### Key endpoints

- `POST /sessions` · `POST /sessions/{id}/stop|mode|vad|wake`
- `POST /process` · `POST /parse` · `POST /commands/{id}/confirm`
- `GET /commands` · `GET /history` · `GET /devices` · `GET /profiles` · `GET /statistics`
- `POST /integrations/ai-runtime|workflow|service-builder|context-engine`

## Database (Alembic `p9j012345678`)

`voice_sessions` · `voice_commands` · `voice_history` · `voice_devices` · `voice_profiles` · `voice_statistics`

ORM: `database/models/voice.py`

## UI

`/platform-builder/voice` (alias `/voice-center`)

Pages: Voice Dashboard · Live Microphone · Sessions · Command History · Device Manager · Voice Profiles · Statistics

## Modules

| Module | Path |
|--------|------|
| Models | `platform_ai/voice_models.py` |
| Providers | `platform_ai/voice_providers.py` |
| Parser | `platform_ai/voice_parser.py` |
| Security | `platform_ai/voice_security.py` |
| Engine | `platform_ai/voice_engine.py` |
| Facade | `platform_ai/voice_service.py` |
| HTTP | `platform_ai/voice_router.py` |
