# Sprint — Odessa Prime Casino first-class platform entry

**Date:** 2026-08-28  
**Branch:** `develop`

Make Odessa Prime Casino a first-class ADOS Enterprise business entry. Canonical route remains `/casino`. No second casino implementation.

## What shipped

- Left nav **Casino** item (`vert_casino`) under Business, immediately below Beauty
- Canonical route `/casino` for nav, search, Enterprise City, and direct URL
- One authoritative search document: Odessa Prime Casino · Casino / Entertainment · AVAILABLE · Open
- City / hub search no longer emit duplicate casino rows; stale `city_casino` / `hub_city_casino` / `idx_casino_lobby` ids are removed on register
- Facade door overlays are invisible hit areas (no pale rectangles, no debug labels)
- Casino bundle stays route-lazy via `lazy(() => import("@/casino"))`; shell stops ambience on unmount; presence leaves the room on unmount

## Architectural decisions

- Extend existing Platform Menu Catalog, module registry, and searchIndex. Do not add a `/workspace/casino` shell.
- City building `casino.route` now points at `/casino` (legacy `/casino/venues/odessa-prime` remains a redirect).
- Casino is not added to `BUSINESS_ECOSYSTEM_KEYS` so search does not invent `/workspace/casino`.
- Python menu keeps `group="verticals"` like Beauty/Cafe; the web bridge maps verticals → Business accordion.

## Intentionally deferred

Facade visual polish and premium game cards (next sprint). Gameplay redesign. Real-money. Recruiting/WhatsApp.
