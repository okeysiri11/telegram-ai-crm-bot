# Sprint CQ-30.1 — Role-Based Navigation UX

**Sprint:** CQ-30.1 — UX Design. Documentation only, `src` not modified.

**Do not duplicate:** real `EngineRoleCode` (`database/models/role.py`: `OWNER/ADMIN/MANAGER/
ACCOUNTANT/LAWYER/PARTNER/OPERATOR/VIEWER`) already matches 7 of this brief's 11 roles by name or
close synonym. This document maps the brief's UX asks onto that real enum rather than inventing a
parallel role taxonomy — extending the same discipline `docs/CITIZEN_ORGANIZATION_MEMBERSHIP.md`
(CQ-12) already established.

**New finding this sprint**: a **third** real, independent role vocabulary exists — frontend
`src/web/auth/managers/roleManager.ts`'s `Role` type (`Platform Owner`/`System Admin`/`Organization
Owner`/`Project Lead`/`Custom Analyst`, scoped `system/organization/project/custom`, with real
inheritance chains and permission groups). This is unreconciled with both `EngineRoleCode` and this
brief's 11 roles — noted here as grounding context, not resolved (per this engagement's standing
discipline of flagging rather than silently merging vocabularies, `docs/TECH_DEBT.md` TD-52 being the
precedent for exactly this kind of finding).

## 1. Per-role UX (brief's eleven)

| Brief role | Real mapping | Visible menus | Hidden menus | Dashboard | Nav flow |
|---|---|---|---|---|---|
| Owner (God Mode) | `EngineRoleCode.OWNER` + frontend `Platform Owner` (`role_platform_owner`) | Everything, including `docs/OWNER_MODE_UX.md`'s full set | None | Real `ExecutiveDashboard`/`MissionControlStrip` (`docs/EXECUTIVE_OPERATING_SYSTEM.md`, CQ-15) | Lands on Owner Dashboard; City Administration, Security Center, Architecture, Developer Tools all one click away |
| Administrator | `EngineRoleCode.ADMIN` | Organization settings, Team, Roles, most operational modules | Platform-wide Owner-only items (§`OWNER_MODE_UX.md` §1) | Real Operations domain dashboard (`docs/OPERATIONAL_DASHBOARDS.md`, CQ-17) | Lands on Operations Dashboard |
| Manager | `EngineRoleCode.MANAGER` | Deals, Projects, Team (own department), Calendar | Org-wide settings, billing, other departments' data | `DashboardScope` filtered to the manager's `Membership.role` scope (`docs/OPERATIONAL_DASHBOARDS.md` §2) | Lands on filtered department dashboard |
| Employee | **No exact `EngineRoleCode` match** — closest real precedent is `OPERATOR` (task-execution-scoped) or a plain `Membership` with no elevated role | Own tasks, own calendar, assigned projects, AI agent (if assigned) | Team management, org settings, financial data | A personal work view — real `ProjectParticipant`/`LifeMeeting` scoped to the citizen | Lands on "My Day" (personal Life Engine view, `docs/DAILY_OPERATIONS_MODEL.md`, CQ-17) |
| Client | **No `EngineRoleCode` match — genuinely external-facing, new UX surface** | Own orders/deals (real `Deal.customer_id`, CQ-18), own documents, support requests | Everything internal | A minimal "my relationship with this company" view | Lands on a client portal, not the main Beta shell — flagged as the least-grounded role in this list, matching `docs/ENTERPRISE_SCENARIO_LIBRARY.md`'s (CQ-17) already-known "non-partner customer contact is thin" gap |
| Dealer | Real `AutomotiveDealerSource`/`DealerSourceType` (`automotive_partner_integration.py`) — vertical-scoped, not a platform-wide role | Vehicle inventory, deal pipeline (their own), commission (real `DealEngineCommission`) | Other verticals entirely | Automotive-vertical dashboard | Lands on the automotive vertical's own Deal Pipeline view |
| Partner | `EngineRoleCode.PARTNER` + real `Relationship`/`BusinessProfile` (Sprint 29.0) | Shared projects/meetings/documents/assets per real Visibility composition (`docs/CROSS_ORG_DAILY_COOPERATION.md` §2, CQ-17) | Everything not explicitly shared | A composed cross-org view, gated by real permission composition | Lands on a "Shared with us" view |
| Lawyer | `EngineRoleCode.LAWYER` | Contracts, `legal_enterprise` vertical (real, `document_intelligence`/`case_management`), compliance | Financial operations, HR | Real `legal_enterprise` dashboard | Lands on Case Management |
| Accountant | `EngineRoleCode.ACCOUNTANT` | Financial modules, real `multi_company`/`IntercompanyTransaction`, billing | Product/engineering modules | A financial summary view | Lands on Financial Operations |
| Production | **No exact match** — closest is `OPERATOR`, scoped to the real 17-studio AI Production Center (`docs/PRODUCTION_STUDIO_UX.md`) | Production Studio, Brand Assets, Pipeline stages | Financial/HR/Security | Real `AIProductionCenterPage.tsx` shell (Studios/Pipeline/Prompts/Media/Automation tabs) | Lands on Production Studio's Pipeline tab |
| Viewer | `EngineRoleCode.VIEWER` | Read-only versions of whatever their `Membership` scope covers | All write actions (buttons hidden or disabled, per real permission checks) | Same dashboard as their scope, read-only widgets | Lands on the same dashboard a Manager/Employee in their scope would see, minus mutation controls |

## 2. Design principle: hidden means absent, not disabled

Consistent with `docs/UI_NAVIGATION.md` §1's Owner-item gating: a menu item a role cannot access should
not render in a disabled state — it should not render at all. This avoids leaking the existence of
features (e.g., a Client should not see a greyed-out "Security Center" link revealing that one exists).
This is a UX principle, not a new permission mechanism — every gate reuses the real composed
`SpatialPermissionScope`/`AssetPermissionScope`/`Visibility` check (`docs/DIGITAL_TWIN_STANDARDS.md`
§3, CQ-16).

## 3. Client and Dealer are the two roles requiring genuinely new UX, not composition

Every other role in §1 composes real, already-designed dashboard/permission pieces. Client and Dealer
are flagged distinctly: Client needs a portal-shaped experience this engagement has never designed
(the closest real precedent, `src/web/portals/`, is confirmed thin per `TD-09`/`docs/ENTERPRISE_FULL_
AUDIT.md`), and Dealer is real but automotive-vertical-only with no platform-wide equivalent. A future
sprint scoping the Beta should treat these two as the highest-uncertainty items in this document.

## Non-goals

- No new role enum or permission engine — every mapping in §1 composes `EngineRoleCode`/`Membership`/
  the real permission-scope composition.
- No resolution of the three-way role-vocabulary collision (backend `EngineRoleCode`, frontend
  `roleManager.ts`, this brief's 11 roles) — flagged, not merged.
- No client-portal implementation designed in depth — flagged as the Beta's highest-uncertainty UX
  surface, not solved here.

## Related documents

`docs/CITIZEN_ORGANIZATION_MEMBERSHIP.md` (CQ-12, real `EngineRoleCode`), `docs/TECH_DEBT.md` (TD-52,
the permission-scope precedent for flagging vocabulary collisions), `docs/OPERATIONAL_DASHBOARDS.md`
(CQ-17, `DashboardScope`), `docs/CROSS_ORG_DAILY_COOPERATION.md` (CQ-17), `docs/OWNER_MODE_UX.md`/
`docs/UX_ARCHITECTURE.md`/`docs/UI_NAVIGATION.md` (CQ-30.1 siblings).
