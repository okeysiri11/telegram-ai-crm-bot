# Creative Factory

Enterprise AI-powered content production platform — Sprint **36.9**.

Canonical SoR: **`platform_ai`** (`creative_*`). Do **not** create `platform_creative`.

## Capabilities

### Creative Studio

Generate:

- Landing Pages · Advertisements · Social Media Posts · Blog Articles · Email Campaigns
- Sales Proposals · Commercial Offers · Presentations · PDF Documents · Marketing Reports

### AI Media Generation

Modalities with provider routing + failover:

| Modality | Providers (ordered) |
|----------|---------------------|
| Text | openai_text → anthropic_text → local_text |
| Image | openai_image → stability_image → local_image |
| Video | runway_video → local_video |
| Voice | elevenlabs_voice → openai_voice → local_voice |
| STT | whisper_stt → local_stt |
| TTS | openai_tts → local_tts |

### Campaign Builder

Objectives, audience, channels, budget, creatives, schedule, analytics.

### Brand Center

Logos, colors, typography, tone of voice, templates, reusable assets.

### Content Library

Images, videos, documents, prompts, templates, generated creatives — versioning + semantic search.

### Publishing Hub

Facebook · Instagram · TikTok · Telegram · LinkedIn · X · YouTube — including scheduled publish.

## REST

| Prefix | Scope |
|--------|--------|
| `/api/creative/*` | Studio, brand, assets, search, publish, integrations |
| `/api/campaigns/*` | Campaign CRUD + analytics |
| `/api/media/*` | Media library + media generate |
| `/management/v1/creative/*` | Management dual-prefix |

## Database

Alembic revision `s2m345678901` (revises `r1l234567890`):

- `creative_projects`
- `creative_assets`
- `creative_templates`
- `campaigns`
- `campaign_channels`
- `media_library`
- `brand_profiles`
- `creative_history`

ORM: `database/models/creative_factory.py`

## UI

`/platform-builder/creative` — Creative Dashboard, Campaign Builder, Brand Center, Media Library, Prompt Studio, Publishing Hub, Analytics.

## Integrations

AI Runtime · Multi-Agent Runtime · Project Memory · Context Engine · Workflow Runtime · Enterprise Event Bus · Voice Command Center · AI Skills & SDK.

## Modules

| Module | Role |
|--------|------|
| `platform_ai/creative_models.py` | Domain models |
| `platform_ai/creative_engine.py` | Studio / media / campaign / publish |
| `platform_ai/creative_service.py` | Façade + integrations |
| `platform_ai/creative_router.py` | HTTP routes |

## Service Builder

`svc_creative_factory` — APIs `/api/creative`, `/api/campaigns`, `/api/media`, `/management/v1/creative`.

## Verify

```bash
.venv/bin/python -m pytest tests/test_creative_factory_36_9.py -vv
```
