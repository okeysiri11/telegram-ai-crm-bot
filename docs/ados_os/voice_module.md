# Enterprise Voice Module (ADOS OS 4.1)

First-class voice interface — equal to Web, Telegram, and API.

```
Microphone → Noise Reduction → VAD → Speech Recognition
  → Intent Detection → ChatGPT Bridge → AI Orchestrator
  → Provider Gateway → Execution → Speech Synthesis
```

## Module

`src/voice` · service id `ados.voice` · package `@ados/voice` 4.1.0

| Component | Role |
|-----------|------|
| `VoiceGateway` | Public facade |
| `SpeechPipeline` | End-to-end audio → task → TTS |
| `VoiceSession` | Start / pause / resume / stop |
| `VoiceRecorder` | Mic frames, NR, VAD |
| `SpeechRecognizer` | OpenAI STT · Whisper · Local Whisper |
| `SpeechSynthesizer` | OpenAI TTS · System Voice |
| `IntentDetector` | 16 enterprise intents |
| `CommandInterpreter` | Bridge tasks + navigation |
| `WakeWord` | Configurable (default “Hey ADOS”) |
| `VoiceContext` | Page / project / sprint / agent memory |
| `VoiceHistory` / `VoiceSettings` / `VoiceEvents` | Audit, config, WS |

## Supported intents

Create Project · Create Task · Open Module · Search · Run Workflow · Generate Code · Review Code · Explain Code · Open CRM / ERP / AI Studio / Marketplace · Create Document · Generate Report · Run Agent · Execute Command

## REST

| Method | Path |
|--------|------|
| POST | `/voice/start` |
| POST | `/voice/stop` |
| POST | `/voice/process` |
| GET | `/voice/history` |
| GET | `/voice/settings` |
| POST | `/voice/settings` |
| GET | `/voice/status` |

Also: `POST /voice/pause`, `POST /voice/resume`.

## WebSocket / Event Bus

`voice.started` · `voice.stopped` · `voice.detected` · `voice.transcribed` · `voice.intent` · `voice.executed` · `voice.response` · `voice.status` · `voice.partial` · `voice.final` · `voice.execution` · `voice.completed`

## Control Center

**Voice Center** (`/voice`): mic status, session, recognized text, intent, confidence, agent, provider, execution, response, history, settings.

## Security

Microphone permission gate · provider auth via STT/TTS connect · session validation on process.

## Boot order

Provider Gateway → Orchestrator → Chat Bridge → **Voice** → Runtime Server
