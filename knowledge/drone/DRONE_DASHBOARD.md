---
title: Drone Dashboard
aliases:
  - Drone Dashboard
tags:
  - drone
  - dashboard
generated: 2026-07-22
sprint: "11.9"
---

# Drone Dashboard

## Overview
Readiness dashboard for Drone Platform through Sprint 11.9 (Production Ready).

## Architecture
Part of [[Drone Platform]].

## Components
- Manufacturing Ready (11.6)
- Mission Operations Ready (11.7)
- Drone Cloud / Enterprise Ready (11.8)
- Navigation Ready (11.9)
- Communications Ready
- Safety Ready
- Recovery Ready
- Health Monitoring Ready
- Drone Platform Production Ready
- Links: [[drone/NAVIGATION_REGISTRY]] [[drone/COMMUNICATION_REGISTRY]] [[drone/SAFETY_REGISTRY]] [[drone/RECOVERY_REGISTRY]] [[drone/CLOUD_DASHBOARD]] [[drone/MISSION_OPS_DASHBOARD]] [[drone/KNOWLEDGE_GRAPH]]

## Relationships
[[Drone Platform]] · [[ARCHITECTURE_DASHBOARD]] · [[INDEX]] · [[Knowledge Graph]]

## Interfaces
Docs: `docs/NAVIGATION.md`, `docs/COMMUNICATIONS.md`, `docs/SAFETY.md`, `docs/RECOVERY.md`, `docs/HEALTH_MONITORING.md`

## REST APIs
`/api/drone/v1/resilience/*`

## Events
drone_resilience_updated
