# Visual Theme Engine

Sprint **29.5** / Platform Builder **v1.12.0** / Theme Engine **1.0**

Controls the complete visual identity of the platform.

**Themes never contain business logic.** Themes affect appearance only.

## Module

Platform Builder → Visual Theme Engine (`/platform-builder/themes`)

API: `/api/platform-builder/v1/themes/*`

## Scopes

- Global Themes
- Organization Themes
- Department Themes
- Workspace Themes
- Future AI City Themes

## Modes

Dark Mode · Light Mode

## Features

- Color System (Primary, Secondary, Accent, Background, Surface, Status, Gradients)
- Enterprise Branding
- Component Theming
- AI Visual Style
- Animation Themes
- Accessibility
- Live Theme Switching (no restart)

## Layout

- Backend: `applications/platform_builder/themes/`
- Frontend: `src/web/platform-builder/themes/`
- Knowledge: `knowledge/themes/`
- Related: [ENTERPRISE_THEMES.md](./ENTERPRISE_THEMES.md)
- Tests: `tests/test_theme_engine_29_5.py`
