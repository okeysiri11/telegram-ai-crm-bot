# 03 — The Enterprise Operating System Concept

**Chapter of the Master Product Bible.** Full detail lives in `ENTERPRISE_NAVIGATION.md` and
`WORKSPACE_INTERACTIONS.md` — this chapter explains *why* those two documents together constitute an
"operating system," not a navigation spec and an interaction spec that happen to sit next to each
other.

## The OS metaphor, made literal

`ENTERPRISE_NAVIGATION.md` §1 states the thesis plainly: **the platform should feel like one operating
system, not a collection of pages.** This chapter names the concrete OS analogs already real in the
platform (`ENTERPRISE_NAVIGATION.md` §0's grounding table has the code-level evidence for each):

| OS concept | ADOS equivalent | Status |
|---|---|---|
| Taskbar / Dock | The real, `localStorage`-persisted Dock system (`shellLayoutStore`) — collapse, pin, auto-hide, resize | **Real** |
| Spotlight / Alt-Tab | The Command Palette (`UniversalCommandPalette`) — 4 modes, 5 keyboard entry points | **Real, but see the gap below** |
| App launcher | The Sidebar, driven by the tenant-filtered application registry | **Real** |
| Notification tray | The Notifications Panel + toast strip | **Real** |
| Windows | Tabs, Dock panels, and (designed) Floating Windows | **Tabs/Dock real; Floating Windows designed** |
| Desktop wallpaper / spatial view | Enterprise City | **Real (2D); 3D is vision** |
| System assistant | The AI Advisor, reachable from Dock, Palette, and (designed) voice | **Real (Dock + Palette); voice designed** |
| Window manager conventions | Drag, multi-select, context menus, undo/redo | **Only real for tabs; not yet generalized** |

## The one concrete crack in the metaphor

`ENTERPRISE_NAVIGATION.md` §0 and §22 identify the platform's most important navigation finding: **two
Command Palettes exist, and one is dead code that never runs.** An operating system with two
Spotlights, only one of which works, is not yet the OS this platform claims to be. This is not a minor
implementation detail — it is the single clearest test of whether the OS metaphor is real or
aspirational today, and it is tracked as `TECH_DEBT.md` TD-40 specifically because of that importance.
A second, related crack: favorites and history are implemented twice with no shared state
(`TECH_DEBT.md` TD-41). Closing both is `10_ROADMAP.md`'s highest-priority near-term item.

## Workspace: where the OS is actually used

If Navigation is the OS's shell, Workspace is its desktop — the post-login home where sustained work
happens (`ENTERPRISE_DESIGN_SYSTEM.md` §15). `WORKSPACE_INTERACTIONS.md` is this chapter's other pillar:
it defines the one interaction language (drag, select, context-act, undo) that should behave
identically whether a user is touching a CRM record, a Production Studio asset, or an Enterprise City
building. Its central finding mirrors Navigation's: most of these interactions are real in exactly one
place (`WorkspaceTabBar.tsx`) and not yet generalized — the OS's "window manager conventions" exist as
a prototype in one corner of the app, not as a platform-wide rule yet.

## Runtime: what actually runs

The OS metaphor describes the user-facing experience; underneath it, the platform's real runtime is a
dual process — a Telegram bot (aiogram) and an aiohttp API server sharing one Postgres database
(`ARCHITECTURE_MAP.md` §2.1, `CLAUDE.md`'s architecture section). This is worth stating plainly here
because it is easy to let the OS metaphor imply a single monolithic desktop-like process — it does not.
The "operating system" is the coherent *experience* layered over this real, more conventional
web-application runtime; `09_ARCHITECTURE.md` covers the runtime's actual shape in full.

## Permissions: who sees which windows

An operating system's permission model decides which apps a user can even open. ADOS's equivalent is
RBAC enforced through `platform_identity`/`platform_management` (`MODULES.md` §4) — it decides which
Sidebar items, which City buildings (`ENTERPRISE_CITY.md` §8's designed role-aware visibility), and
which Workspace modules a given user sees at all. This is designed to be the single source of truth
for visibility everywhere — a City building's visibility, a Sidebar item's visibility, and a Workspace
module's visibility should all read from one permission decision, never three independently-maintained
visibility lists (a specific instance of `02_PRODUCT_PHILOSOPHY.md` principle 7).

## Related chapters

`04_ENTERPRISE_CITY.md` (the OS's spatial desktop), `05_AI_PRODUCTION.md` (a major application running
inside this OS), `09_ARCHITECTURE.md` (the real runtime/permission mechanics behind this chapter's
product-level description), `10_ROADMAP.md` (closing the palette/favorites cracks named above).
