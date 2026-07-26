# Unified Enterprise Workspace — Sprint 32.3.6

## Purpose

Единое Enterprise OS ощущение: глобальный контекст, Quick Switch, breadcrumbs, search, shortcuts — без новых Engine.

## Global Workspace Context

В shell (`FullLayout`):

- Workspace / organization (`company`, `project`)
- Role (first-entry / auth)
- Active ecosystem (from path)
- AI Concierge name
- Workspace status

## Quick Switch

Chips: Dashboard · Mission Control · City · CRM · Analytics · Documents · AI Team · Knowledge · Settings  
+ Ctrl+Tab Quick Switcher (`enterprise` pool)

## Breadcrumbs

`Enterprise › …` via enhanced `breadcrumbEngine` + `labelForSegment`.

## Search

`registerUnifiedWorkspaceSearch()` upserts modules / ecosystems / users / AI / docs into existing `searchIndex` (⌘K).

## Keyboard

| Shortcut | Action |
|----------|--------|
| Ctrl/⌘+K | Command palette / search |
| Ctrl/⌘+/ | Omnibox commands |
| Ctrl+Tab | Quick Switcher |
| Esc | Close panels |

## Notifications

`UnifiedToastStrip` + labeled `NotificationsPanel` over existing `notificationStore`.

Platform Builder **v1.48.0**.
