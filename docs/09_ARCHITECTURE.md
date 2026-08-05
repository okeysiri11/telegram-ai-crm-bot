# 09 — Architecture, Modules, Verticals, Marketplace, Runtime & Permissions

**Chapter of the Master Product Bible.** This chapter is a pointer chapter over the platform's deepest
technical documentation set: `ARCHITECTURE_MAP.md`, `DEPENDENCY_MAP.md`, `MODULES.md`, `API_MAP.md`,
`TECH_DEBT.md`. It exists so a product-level reader (or an AI agent doing product work) gets the shape
of the engineering reality without needing to read five long specs first — and so an engineering reader
knows exactly which of those five to open for depth.

## The shape of the platform, in one paragraph

ADOS is three largely independent systems sharing one repository (`ARCHITECTURE_MAP.md` §0): a Python
Telegram-bot-plus-enterprise-backend (repo root, ~106 `platform_*` capability packages,
`ARCHITECTURE_MAP.md` §2), a set of 17 business-vertical applications and two web consoles built on top
of it (`applications/*`, `src/web`, `platform_console`), and a standalone Node/TypeScript "ADOS OS"
agent-kernel runtime (`src/kernel` + six packages) with no runtime connection to the other two. This
last fact is not a defect to hide — it is stated plainly in the architecture map and repeated here
because a Bible that omitted it would mislead any future contributor into assuming more integration
exists than actually does.

## Modules

~106 `platform_*` capability packages, 17 vertical `applications/*`, catalogued individually in
`MODULES.md` with purpose, owner, public API, dependencies, status, tech debt, and future plans for
each. The Bible-level takeaway: most naming collisions across this module set (multiple "orchestrator,"
"memory," "workflow," "dashboard" implementations) are **deliberately additive per the platform's own
policy** (`docs/TECHNICAL_DEBT_REPORT.md`'s explicit non-action: "do not merge vertical apps") — a
future contributor should read `TECH_DEBT.md`'s duplicate-code section before assuming a same-named
module elsewhere is redundant or safe to delete.

## Verticals

17 vertical applications (`MODULES.md` §8) ranging from GA production scale (`auto_marketplace`, 420
files) to thin scaffolding (`ai_os`, `ecosystem`, `executive_center`, 14–20 files each). Each vertical
gets its own API prefix family (`API_MAP.md` §1.5) and, per `ENTERPRISE_CITY.md` §23's scaling model,
each vertical's visibility in the City/Sidebar/Workspace is meant to track one shared per-tenant
enablement source, never a per-surface enablement list maintained three separate times.

## Marketplace

Marketplace is not one module — it is a pattern repeated per vertical (`auto_marketplace`,
`agro_marketplace`, `applications/marketplace`, plus vertical-embedded storefronts in `port_erp` and
others). A proposed unifying "Marketplace Plaza" City building (`ENTERPRISE_CITY.md` §9.2) and the
Production Studio's Social Content Studio (`AI_PRODUCTION_STUDIO.md` §13) both point at this same
underlying reality: marketplace commerce is a cross-cutting concern touched by many verticals, not a
single owned subsystem — any future consolidation work here is a real architectural decision, not a
rename.

## Runtime

The real, shipped runtime is a dual process: an aiogram Telegram bot and an aiohttp API server sharing
one Postgres database, started together from `startup.py` (`ARCHITECTURE_MAP.md` §2.1,
`03_ENTERPRISE_OS.md`). `docker-compose.yml` currently defines only `postgres`+`redis` — no unified
deploy story for the application processes exists yet (`TECH_DEBT.md` TD-14). The separate TypeScript
kernel runtime (`src/kernel`'s `RuntimeServer`, port 3000) is real, non-trivial code with exactly one
consumer (`platform_console`) and zero connection to this Python runtime (`ARCHITECTURE_MAP.md` §15
item 5, `TECH_DEBT.md` TD-33) — whether that TypeScript runtime becomes part of the "one operating
system" story (`03_ENTERPRISE_OS.md`) or stays a separate product is an open, undocumented decision.

## Permissions

RBAC is enforced through `platform_identity`/`platform_management` (`MODULES.md` §4) — today
header-only pending a full live token round-trip (`TECH_DEBT.md` TD-08). This is the single source of
truth `03_ENTERPRISE_OS.md` designates for every visibility decision in the product experience (Sidebar
items, City buildings, Workspace modules, Studio approval reviewer roles) — a feature that maintains its
own separate permission list instead of reading from this system is a defect, not a valid shortcut.

## The four governance facts worth stating in the Bible directly

1. **4 critical architecture violations currently fail CI** (`platform_security` bypassing
   `ConfigurationCenter`, `ARCHITECTURE_MAP.md` §11.1) — the one item in the entire technical
   documentation set that is an outright policy violation with an active enforced gate, not a judgment
   call.
2. **0 circular dependencies** in the governed Python graph (`DEPENDENCY_MAP.md` §8) — a real, positive
   architectural fact worth stating alongside the violations above, not just the problems.
3. **The legacy boundary (`platform_legacy/`) is real and load-bearing**, but is itself violated by
   code that's supposed to be on the modern side of it (`database/__init__.py` importing
   `database_legacy`, `TECH_DEBT.md` TD-19/TD-25) — the platform's own isolation mechanism has a leak.
4. **Two Command Palettes and two favorites systems** (`TECH_DEBT.md` TD-40/TD-41) are the frontend
   equivalent of the same "governance boundary has a leak" pattern — named again here because it is
   this platform's clearest example of a principle (`02_PRODUCT_PHILOSOPHY.md` #7) not yet fully lived
   up to.

## Related chapters

`03_ENTERPRISE_OS.md` (the runtime/permissions story at product level), `10_ROADMAP.md` (sequencing the
governance fixes named above), and the five underlying documents this chapter summarizes —
`ARCHITECTURE_MAP.md`, `DEPENDENCY_MAP.md`, `MODULES.md`, `API_MAP.md`, `TECH_DEBT.md` — for anything
beyond this summary.
