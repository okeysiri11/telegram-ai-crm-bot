# Sprint CQ-30.7 — First-Time User Evaluation

**Question:** can a first-time user understand the platform and find CRM, ERP, Knowledge, Production
Studio, Marketplace, Analytics, Settings? Documentation only, `src` not modified.

## Direct answer, per module (against the real, current sidebar)

| Module | Findable? | Evidence |
|---|---|---|
| CRM | **Yes** | `{ id: "crm", label: "CRM", route: "/crm" }` — English acronym kept as-is, immediately recognizable to a business user |
| ERP | **Yes** | Same pattern, `{ id: "erp", label: "ERP", route: "/erp" }` |
| Knowledge | **Yes, with one caveat** | Real sidebar item "Знания" (`/knowledge`) is findable; a separate Owner-only "Граф знаний" (`/platform-builder/knowledge`) exists at a *different* route — a first-time non-Owner user only sees the first, so no confusion for them specifically, but `docs/OWNER_EXPERIENCE.md` §1 flags the two-route split as an Owner-specific risk |
| Production Studio | **Yes** | "Продакшн" (`/production-studio`) — findable, though the label alone doesn't signal "AI content generation" to a first-time user; see recommendation below |
| Marketplace | **Findable, but mislabeled elsewhere** | The sidebar item itself ("Маркетплейс") is correct and findable; breadcrumbs/search results for the same page show "Маркетинг" instead — **this is `docs/UX_AUDIT.md`'s headline bug**, directly answering this exact brief question with a concrete failure mode: a user who searches for the module rather than scanning the sidebar gets the wrong label |
| Analytics | **Yes** | "Аналитика" (`/analytics`) — clear, standard term |
| Settings | **Yes** | "Настройки" (`/settings`) — clear, standard term, consistent with real `messages.ts`'s `nav.settings` |

**Six of seven are cleanly findable on first look. The seventh (Marketplace) is findable via the
sidebar but actively misleading via search and breadcrumbs** — this is the single most important
finding this review can offer in direct response to the brief's own evaluation question.

## Can a first-time user understand the platform overall?

Largely yes, with two qualifications:

1. **Главная (Home) vs. Рабочий стол (Desktop)** — two real, distinct landing-adjacent routes with
   names that don't self-explain the difference (`docs/NAVIGATION_REVIEW.md` §3). A first-time user
   would likely need to click both to understand the distinction, rather than inferring it from labels
   alone.
2. **Production Studio's real status is not communicated by its label** — "Продакшн" doesn't indicate
   this is currently a UI preview with no real generation backend (`docs/TECH_DEBT.md` TD-45,
   `docs/PRODUCTION_STUDIO_UX.md` §3, CQ-30.1). A first-time user exploring this module would encounter
   the honesty gap this engagement has flagged repeatedly, at the exact point of first contact.

## First login specifically

`docs/LOGIN_USER_FLOW.md`'s (CQ-30.1) already-identified Registration/Invitation gap is the literal
first thing a prospective first-time user encounters — if unresolved, "can a first-time user understand
the platform" is moot because they can't get in. Restated here as this document's own top blocker,
not re-derived.

## Recommendation

1. Fix the Marketplace mislabeling (P0, shared with `docs/UX_AUDIT.md`).
2. Add a one-line distinguishing subtitle under "Рабочий стол" in the sidebar tooltip (P3).
3. Add a real-status badge to Production Studio's sidebar entry or landing screen, not just individual
   studio cards (extends `docs/PRODUCTION_STUDIO_UX.md` §3's card-level recommendation to the
   navigation entry point itself, so the honesty signal reaches a user before they even open the
   module).

## Non-goals

- No onboarding-flow redesign — `docs/BETA_USER_JOURNEY.md` (CQ-30.7 sibling) covers the full journey;
  this document is scoped to the specific seven-module findability question the brief asked directly.

## Related documents

`docs/UX_AUDIT.md`/`docs/NAVIGATION_REVIEW.md`/`docs/BETA_USER_JOURNEY.md` (CQ-30.7 siblings),
`docs/LOGIN_USER_FLOW.md`/`docs/PRODUCTION_STUDIO_UX.md` (CQ-30.1), `docs/TECH_DEBT.md` (TD-45).
