# Enterprise Design System

**Version:** `9.0.1` · **Sprint:** 26.2  
Path: `src/web/design-system`

Centralized tokens, colors, typography, icons, grid, spacing, elevation, animation, responsive, accessibility, component catalog, and theme engine for the Enterprise Web Platform.

## Architecture

```
design-system/
├── tokens/          # Colors, fonts, sizes, radii, shadows, spacing, z-index, breakpoints, motion, opacity
├── colors/          # Semantic color system (primary…focus)
├── typography/      # Display → button text scale
├── icons/           # Navigation, AI, CRM, ERP, Finance, HR, Analytics, Notifications, Security, Settings, Workflow
├── grid/            # 12-col, responsive, fluid/fixed, dashboard, workspace
├── spacing/         # Spacing scale
├── elevation/       # Shadows + z-index levels
├── animation/       # Fade, slide, scale, collapse, expand, page, loading, skeleton, micro
├── responsive/      # Mobile / tablet / laptop / desktop
├── accessibility/   # WCAG AA, keyboard, SR, focus, high contrast, reduced motion
├── catalog/         # Component catalog (API, props, examples, rules, a11y)
├── theme/           # Light / dark / corporate / custom branding
├── docs/            # Auto-generated design documentation
└── styles/tokens.css
```

## Usage

```ts
import { tokens, Icon, applyTheme, generateDesignDocumentation } from "../design-system";
```

CSS variables are prefixed `--eds-*`. Web Foundation aliases `--ew-*` map to the same tokens.

## Hub

- Library: `platform_enterprise_design_system/`
- Suite: `enterprise_hub.design_system`
- API: `/api/enterprise-eds/v1`
