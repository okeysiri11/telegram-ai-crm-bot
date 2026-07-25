# Enterprise AI Builder

Sprint **28.2** / Platform Builder **v1.1.0** — complete visual wizard for creating AI specialists.

## Location

Platform Builder → AI Builder (`/platform-builder/ai`)

API: `/api/platform-builder/v1/ai-builder/*`

## Wizard steps

1. Number of AI Agents (1 / 2 / 3 / 5 / 10 / 20 / Custom) + multi-agent explanation
2. AI Agent Name (custom + suggested Male / Female / Neutral) + live preview
3. Profession catalog
4. Specialization tree (expandable, multi-select)
5. Knowledge sources with plain-language help
6. Skills
7. Permissions (visual selector)
8. Personality + conversation preview
9. Summary AI Card
10. Create → save configuration → register in AI Registry

## Multi-agent

One session can create several specialists. Slot switcher appears when count > 1.

## Group AI Chat

Foundation architecture only (`GET /ai-builder/group-chat`). Runtime chat arrives later.

## Help & Academy

Uses Builder Framework, Builder Academy, and positive Help System (Purpose / Benefits / Example).

## Tests

`tests/test_ai_builder_28_2.py`
