# Architecture Ownership Glossary — Sprint 30.3

Resolves naming contradictions without merging runtimes. **One name → one owner → one primary route.**

## Ecosystem layers (keep all three)

| Name | Owner path | API | Role |
|------|------------|-----|------|
| Root Ecosystem | `ecosystem/` | `/api/ecosystem/v1` | Identity, workforce, governance, assistant |
| Unified AI Ecosystem | `applications/ecosystem/` | `/api/ai-ecosystem/v1` | Cross-app integration facade (alpha) |
| Business Ecosystem Foundation | `applications/platform_builder/business_ecosystem/` | `/api/platform-builder/v1/business-ecosystem/*` | Industry capability catalogs & extension registry |

Do **not** merge packages. Route by prefix.

## Mission / Command / Twin

| Term | Primary owner | Route / API | Do not confuse with |
|------|---------------|-------------|---------------------|
| Mission Control (Enterprise) | PB `mission_control` | `/platform-builder/mission-control` | Drone mission center; Executive Center |
| Command Center (Global UI) | `src/web/command-center` | `/command-center` | PB Command Center OS |
| Command Center OS | PB `command_center` | `/platform-builder/command-center` | Global Command Center |
| Digital Twin (Enterprise mirror) | PB `digital_twin` | `/platform-builder/digital-twin` | Hub EDT; drone twin |
| Twin Intelligence | PB `twin_intelligence` | `/platform-builder/twin-intelligence` | Scenario analysis only |

## Recommendation / Strategy / Simulation engines

| Term | Distinct owners | Rule |
|------|-----------------|------|
| recommendation_engine | PB intelligence, platform_learning, services/pg_*, vertical apps | Namespace by package; never “one engine to rule them” rewrite |
| strategy_engine | PB strategy vs `crypto_enterprise/strategy_engine` | Domain-scoped |
| simulation | PB visual simulation vs hub ESI vs drone | Domain-scoped |

## AI OS prefix

| Sub-owner | Prefix | Rule |
|-----------|--------|------|
| `applications/ai_os` | `/api/ai-os/v1` (kernel) | Document path tables |
| Enterprise Hub MAOS | `/api/ai-os/v1/maos/*` (hub) | No new prefix; keep subpaths |

## Global cores (immutable — industry only extends)

Mission Control · Digital Twin · Workflow Engine · Knowledge Graph · AI OS · Builder Studio
