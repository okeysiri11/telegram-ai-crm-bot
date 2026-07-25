# Visual Asset Registry

Sprint **29.6** / Platform Builder **v1.13.0** / Visual Asset Registry **1.0**

Central registry that stores, manages, versions, and distributes every visual asset.

**Business logic is completely separated from visual assets.**

## Module

Platform Builder → Visual Asset Registry (`/platform-builder/assets`)

API: `/api/platform-builder/v1/assets/*`

## Supported types

Images · Icons · Avatars · Illustrations · Animations · Effects · Themes · Future AI City Assets

## Categories

AI · Departments · Organizations · Buildings · Documents · Tasks · Knowledge · Workflow · Marketplace · UI Components

## UI

- Asset Browser
- Preview Panel
- Category Explorer
- Version History
- Search & Filters

## Layout

- Backend: `applications/platform_builder/assets/`
- Frontend: `src/web/platform-builder/assets/`
- Knowledge: `knowledge/assets/`
- Related: [RESOURCE_MANAGEMENT.md](./RESOURCE_MANAGEMENT.md)
- Tests: `tests/test_asset_registry_29_6.py`
