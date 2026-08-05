# Beta Release Notes — Closed Beta RC

**Sprint:** 31.0 · Enterprise Web Closed Beta  
**Date:** 2026-08-01

## Highlights

- Full first-run: organization/workspace, language (RU default), platform roles
- Role dashboards: Owner, Admin, **Manager**, **Employee**, Client, Dealer
- Business modules operational (CRM, Projects, Knowledge, Calendar, Notifications, Drive, Marketplace)
- AI Studio / Production Studio / City / Runtime integrated in navigation
- AI prompt firewall + infra hardening from Sprint 30.9

## Known limits

- Heuristic prompt firewall (not an LLM classifier)
- TLS must be enabled by operators
- Some vertical pilots (Cafe/Beauty) share sprint numbers — see collision notes in RESULT docs

## Upgrade notes

Bump `webConfig.sprint` to `31.0`. Rebuild web dist before compose deploy.
