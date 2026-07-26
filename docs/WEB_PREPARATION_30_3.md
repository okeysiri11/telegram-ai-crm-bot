# Web Preparation — Sprint 30.3

Prepares shared Web surfaces for the next **Web implementation** sprint. Composes existing EDS, Workspace layout, and Platform Builder hubs — **no parallel UI architecture**.

## Shared layouts (reuse)

| Layout | Path | Use |
|--------|------|-----|
| FullLayout | `src/web/src/layouts/FullLayout.tsx` | Shell + sidebar |
| WorkspaceLayout | `src/web/src/layouts/WorkspaceLayout.tsx` | Workspace context badges |
| PortalLayout | `src/web/portals/PortalLayout.tsx` | Customer/Employee/Owner portals |
| PlatformBuilderLayout | PB layouts | Builder / executive hubs |

## Portal shells (new composition)

| Portal | Route | Extends |
|--------|-------|---------|
| Customer Portal | `/portals/customer` | PortalLayout + universal modules links |
| Employee Portal | `/portals/employee` | PortalLayout |
| Owner Portal | `/portals/owner` | PortalLayout |
| Mission Control entry | `/portals/mission-control` | Redirect to existing PB Mission Control |

## Workspace module shells (soft-route fix)

| Route pattern | Page |
|---------------|------|
| `/workspace/crm` | WorkspaceModulePage |
| `/workspace/erp` | WorkspaceModulePage |
| `/workspace/finance` | WorkspaceModulePage |
| `/workspace/analytics` | WorkspaceModulePage |
| `/workspace/marketplace` | WorkspaceModulePage |
| `/workspace/ai` | WorkspaceModulePage |
| `/workspace/auto` · `/agro` · `/beauty` | Industry module shells |
| `/workspace/hr` · docs · reports · workflows | Module shells |

Each shell states readiness, links to Platform Builder / APIs / portals — **does not** reimplement CRM/ERP.

## Design system / navigation / dashboards / forms

- EDS unchanged — portals use existing `Badge`, `Card`, `Button`  
- Navigation: Command Center OS labeled distinctly; portal menu entries added  
- Dashboards: continue Workspace dashboards + Mission Control  
- Forms: next sprint binds to live APIs  

## Ready vs next sprint

| Ready now | Next Web sprint |
|-----------|-----------------|
| Shells + routes + nav | Live identity tokens |
| Soft-route reconciliation | Automotive customer/dealer data views |
| Mission Control reuse | Vertical-specific forms against `/api/auto/v1` |
