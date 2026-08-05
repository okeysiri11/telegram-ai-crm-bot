# Enterprise Interaction Runtime

**Sprint:** 29.6  
**Package:** `src/web/src/runtime/interactionRuntime`  
**Constraint:** Runtime-driven · no game mechanics · no hardcoded UI flows · reusable by Web/Desktop/Mobile/2D/3D.

## Purpose

Interaction layer between users, AI, and the living Enterprise City. Every action executes real Runtime operations (Spatial · Viz · Life · EBN · Assets · Workflow · Automation).

## Core

| Component | Role |
|-----------|------|
| InteractionRuntime | Facade |
| InteractionRegistry | Object kinds + context action catalog |
| InteractionContext / Session | Actor · surface · focus · path |
| InteractionHistory | Audit trail |
| InteractionPermissions | Action ACL |
| SelectionEngine | Single · multi · area · hierarchy |
| NavigationEngine | Search · nearby · business discovery · quick jump |
| Context actions | Open · workflow · task · meeting · partner · AI |

## Events

`ObjectSelected` · `ObjectOpened` · `ActionExecuted` · `WorkflowStarted` · `NavigationChanged` · `ContextChanged` · `SelectionChanged`

EventBus: `interaction_runtime_update`.

## UI / API

- Foundation UI: `/interactions` (not final design)
- REST: `/api/enterprise-interaction/v1`
- Bridge: `enterprise-city/cityInteractionBridge.ts`
