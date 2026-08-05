# Sprint CQ-30.7 — UX Audit

**Mode:** Chief Product Officer / Enterprise UX Architect / SaaS Platform Designer review, performed
while Cursor implements Sprint 30.7 in parallel. Documentation only, `src` not modified, no
implementation. Every finding is evidence-based, sourced from the real, current
`src/web/src/navigation/enterpriseRuNav.ts` (Sprint 30.2/30.7, "Single source for sidebar, owner mode,
roles, search categories, quick actions") — not from this engagement's own prior SPEC documents, which
have since been superseded by this real implementation.

## Headline finding: a real, systemic terminology bug — Маркетплейс vs. Маркетинг

The real sidebar has two separate top-level entries that both route to `/marketplace`:

```ts
{ id: "marketplace", label: "Маркетплейс", route: "/marketplace", icon: "marketplace" },
{ id: "marketing", label: "Маркетинг", route: "/marketplace", icon: "marketplace" },
```

"Маркетплейс" (Marketplace) and "Маркетинг" (Marketing) are two distinct, unrelated Russian business
terms — a first-time user clicking "Маркетинг" expecting a marketing/campaigns module lands on the
Marketplace instead. This is not a one-off typo: the same mislabeling is systemic across all three
real label dictionaries in the same file — `MODULE_LABEL_RU.marketplace: "Маркетинг"`,
`BREADCRUMB_LABEL_RU.marketplace: "Маркетинг"`, and `SEARCH_CATEGORY_RU.marketplace: "Маркетинг"` all
label the `marketplace` module id as "Marketing," not "Marketplace." Only the sidebar's dedicated
`marketplace` entry gets the correct label — the breadcrumb trail, search results, and module-title
overlay for the *same page* all show "Маркетинг" instead. A user would see conflicting labels for the
identical screen depending on which UI surface they're looking at.

- **Why:** two Russian words for two different business concepts were mapped to the same code path,
  and the label dictionaries (breadcrumb/search/module-title) were never updated to match the sidebar's
  own correct label.
- **Impact:** direct comprehension failure for the exact module (Marketplace) the brief explicitly asks
  this review to confirm is findable — a first-time user following the breadcrumb or search result
  would not recognize they're looking at the Marketplace.
- **Priority:** P0 — this is a Beta-blocking, one-file fix.
- **Complexity:** S — three dictionary values in `enterpriseRuNav.ts`, no route or component change.
- **Evidence:** `src/web/src/navigation/enterpriseRuNav.ts`, real `ENTERPRISE_RU_SIDEBAR`/
  `MODULE_LABEL_RU`/`BREADCRUMB_LABEL_RU`/`SEARCH_CATEGORY_RU` constants, lines cited above.

## Navigation-level findings

### Documentation drift: `UI_NAVIGATION.md`'s own prose undercounts the real sidebar

`docs/UI_NAVIGATION.md`'s "Primary sidebar (Russian)" line lists 17 items; the real
`ENTERPRISE_RU_SIDEBAR` array it claims to document has **23**. Missing from the doc's prose: Клиенты,
Задачи, Знания, Календарь, Уведомления, Маркетплейс (as distinct from Маркетинг), Пользователи.

- **Why:** the doc's summary line was written once and not kept in sync with the canonical catalog it
  points to.
- **Impact:** a developer or AI agent reading only the doc (not the code) would materially undercount
  the real navigation surface.
- **Priority:** P2.
- **Complexity:** S — resync one line.
- **Evidence:** `docs/UI_NAVIGATION.md` line 18 vs. `enterpriseRuNav.ts:15-37`.

### Near-duplicate sidebar entries: CRM and Клиенты (Clients)

`{ id: "crm", route: "/crm" }` and `{ id: "clients", label: "Клиенты", route: "/crm?view=clients" }`
are two separate top-level sidebar entries pointing at the same page with a different query param. A
first-time user has no way to know, from the sidebar alone, that "Клиенты" is a filtered view of CRM
rather than a separate module.

- **Why:** likely intentional (a shortcut to a common CRM view), but not labeled as such.
- **Impact:** minor comprehension cost, not a functional bug — a user clicking either finds real content.
- **Priority:** P3.
- **Complexity:** S — a visual sub-item indent or shared icon would resolve the ambiguity cheaply.
- **Evidence:** `enterpriseRuNav.ts:19,22`.

### Owner Dashboard and "God Mode" are two distinct real destinations

`OWNER_RU_NAV` has both `owner_home` (`/owner`, "Панель владельца") and `owner_god` (`/platform-
builder/god-mode`, "God Mode") as separate real routes — the brief's own framing ("Owner (God Mode)")
treats these as one concept; the real implementation has split them into two.

- **Why:** likely reflects two real, differently-scoped systems (`docs/OWNER_MODE_UX.md`'s composite
  Owner Dashboard vs. a Platform Builder-specific God Mode surface).
- **Impact:** ambiguous for a first-time Owner — which one is "the" Owner experience?
- **Priority:** P1 — directly relevant to `docs/OWNER_EXPERIENCE.md`'s core question.
- **Complexity:** S to document the intended relationship; M if UX consolidation is warranted.
- **Evidence:** `enterpriseRuNav.ts:40,52`.

## AI Agent experience — brief spot-check

The real sidebar has one dedicated `ai_agents` entry (`/ai-agents`) plus a separate Owner-only "Среда
AI" (`/ai-agents`, same route, Owner-scoped framing) and "Граф знаний" (`/platform-builder/knowledge`).
Findable, single real destination for the base experience — no duplicate-screen issue found here,
unlike Marketplace. Deeper AI Agent UX detail (agent cards, conversation, memory) remains as specified
in `docs/UX_ARCHITECTURE.md` §2 (CQ-30.1), not re-derived in this pass.

## Onboarding — confirmed real, not missing

A real `src/web/src/onboarding` directory and `ExternalPilotOnboardPage.tsx` exist, and
`BREADCRUMB_LABEL_RU` has real entries for `"onboarding"`/`"first-entry"` — correcting any assumption
that onboarding is entirely unbuilt. Depth of this real onboarding flow was not evaluated screen-by-
screen in this pass; see `docs/FIRST_TIME_USER.md` for the first-login-specific evaluation.

## Non-goals

- No redesign of the sidebar structure — findings are terminology/labeling fixes and documentation
  drift, not a structural navigation overhaul.
- No re-litigation of Client/Dealer role gaps already tracked in `docs/ROLE_NAVIGATION.md` (CQ-30.1) —
  see `docs/CLIENT_EXPERIENCE.md`/`docs/DEALER_EXPERIENCE.md` for this sprint's fresh evidence on those.

## Related documents

`src/web/src/navigation/enterpriseRuNav.ts` (real, the canonical source for every finding above),
`docs/UI_NAVIGATION.md`/`docs/CITY_NAVIGATION.md` (real, Sprint 30.2/30.4), `docs/NAVIGATION_REVIEW.md`/
`docs/OWNER_EXPERIENCE.md`/`docs/RUSSIAN_LOCALIZATION_REVIEW.md` (CQ-30.7 siblings).
