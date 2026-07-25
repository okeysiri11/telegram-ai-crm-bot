# AI Guide

Sprint **28.6** / Platform Builder **v1.5.0**

Builder AI Guide coaches users inside every Platform Builder.

## Functions

1. Explain current step
2. Recommend configuration
3. Answer Builder questions
4. Suggest improvements
5. Warn about missing components

## API

- `POST /api/platform-builder/v1/academy/v2/guide` — full coach payload
- `POST /api/platform-builder/v1/academy/v2/guide/ask` — single question

## Behavior

Adapts language density to experience level (Beginner → Expert).

Records Q&A in AI Guide message store for Academy progress (AI Coach User achievement).

## Layout

- Backend: `applications/platform_builder/academy_v2/ai_guide.py`
- Knowledge: `knowledge/platform_builder/guide/`
- Tests: `tests/test_ai_guide_28_6.py`
