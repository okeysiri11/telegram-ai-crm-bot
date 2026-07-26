# Consolidation Inventory — Sprint 30.3

Structured answers for every major subsystem. Detail remains in Sprint 30.2 audit; this table is the consolidation snapshot.

| Subsystem | Implemented | Partial | Architecture-only | Forgotten/planned | Duplicated | Reuse | Merge? | Independent? | Before Web | Before Prod | Blocks testing |
|-----------|-------------|---------|-------------------|-------------------|------------|-------|--------|--------------|------------|-------------|----------------|
| API Core | Gateway + versioned apps | Envelopes | Unified PB OpenAPI | Legacy CRM migration | Health endpoints | EAS | No | Yes per app | Auth contracts | Freeze | Header auth |
| Event Bus | Hub + events/ | Schema gov | Global bus topo | — | Naming styles | Hub EVP | Docs only | Yes | — | Schema enforce | — |
| Workflow Engine | Studio + hub + PB analysis | Boundaries | — | — | Analysis vs exec | Keep boundary | No | Yes | — | — | Confusion |
| Knowledge Graph | EKP/EKG | Industry packs | — | — | Multiple KG | Extend packs | No | Yes | — | — | — |
| Mission Control | PB hub **I** | — | — | — | Name overlap | Glossary | No | Yes | Portal entry ✓ | — | — |
| Digital Twin | PB + hub + drone | — | — | — | Name overlap | Glossary | No | Yes | — | — | — |
| Workspace | Web + PB OS | Soft modules | — | Soft routes | — | Shells ✓ | No | Yes | Soft routes ✓ | — | Dead links fixed |
| AI Platform | Concierge/Team/… | CS weak | — | CS binding | Agent stubs | Binding matrix ✓ | No | Yes | Identity | Agent certify | Stubs |
| Navigation | Web + PB intel | Soft links | — | — | CC labels | Labels ✓ | No | Yes | Done-ish | — | Soft links |
| Auth/RBAC | UI + DB RBAC | Live tokens | — | WebAuthn | Login re-export OK | Identity Center | No | Yes | Token bridge | Token bridge | E2E auth |
| Notifications | Channels docs | Unified | — | — | — | Extend | No | Yes | — | — | — |
| Caching | In-memory flags | Distributed | HA claims | Real backends | — | Behind interfaces | No | Yes | — | Real cache | — |
| Shared UI/EDS | **I** | — | — | — | — | Portals ✓ | No | Yes | — | — | — |
| Business Ecosystems | Catalogs + vertical APIs | Beauty/Cafe | Cafe app | Cafe product | Three ecosystem layers | Glossary ✓ | No | Verticals yes | Portal shells ✓ | Pilot vertical | Cafe |
| Frame builders | Thin frames | — | Full CRM/ERP UI | Fill via UBF | — | UBF | No | Yes | Later | — | — |

## Business vision preservation

Original Automotive / Agriculture / Beauty / Cafe / Crypto / Legal / Drone concepts remain catalogued and (where apps exist) API-backed. **Nothing removed.** Cafe remains the largest product gap.
