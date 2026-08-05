# Sprint CQ-30.7 — Client Experience Review

**Scope:** review Client Mode. Documentation only, `src` not modified.

## 1. What's real: a Client role switcher entry, nothing behind it yet

`enterpriseRuNav.ts`'s real `ROLE_SWITCHER_OPTIONS` includes `{ id: "client", label: "Клиент",
roleIds: ["client"] }` — the role exists in the switcher UI. Confirmed this sprint, consistent with
`docs/ROLE_NAVIGATION.md`'s (CQ-30.1) prior finding: **no dedicated Client navigation array exists** —
unlike Owner's 13-item curated nav, a user switched into Client role sees... what, exactly, was not
confirmed this pass. This is the central open question for Client Experience.

- **Why it matters:** the brief explicitly asks to review Client experience; the honest answer is that
  the *switcher* is real but the *experience* behind it has no confirmed dedicated design in the real
  navigation catalog.
- **Impact:** High — if Beta includes any real external client users, this is the single least-defined
  persona in the entire navigation system.
- **Priority:** P0 for verification (confirm what a Client role actually renders today), P1 for design
  work once confirmed.
- **Complexity:** S to verify current behavior; L to design/build a real client-appropriate view if the
  current behavior is "the full internal sidebar, minus some items" (inappropriate for an external
  user who shouldn't see internal navigation density at all).
- **Evidence:** `enterpriseRuNav.ts`'s `ROLE_SWITCHER_OPTIONS`, absence of a `CLIENT_RU_NAV` or
  equivalent array in the same file.

## 2. Real data a Client experience could ground on

Not absent everywhere — real `Deal.customer_id` (`docs/ENTERPRISE_VALUE_CHAIN.md`, CQ-18) links a real
deal to a real customer user, and real `BusinessProfile`/`Company Card` (`ENTERPRISE_BUSINESS_
NETWORK.md`, CQ-10) could back a "my relationship with this company" view. The gap is entirely on the
navigation/screen side, not the underlying data model — a genuinely buildable gap, not a research one.

## 3. Terminology check

Real `SEARCH_CATEGORY_RU`'s `clients: "Клиенты"` and the sidebar's own `clients` item both use
"Клиенты" consistently — no terminology inconsistency found for the word "Client" itself (unlike
Marketplace/Marketing). The problem is architectural (no dedicated view), not linguistic.

## 4. Recommendation

Do not attempt to give Client a full curated navigation array matching Owner's complexity for Beta —
per `docs/ENTERPRISE_SCENARIO_LIBRARY.md`'s (CQ-17) already-identified "non-partner customer contact is
thin" finding and `docs/ROLE_NAVIGATION.md`'s (CQ-30.1) recommendation, a minimal portal-shaped
experience (own deals, own documents, support contact) is the right Beta scope — not a smaller version
of the internal shell.

## Non-goals

- No client portal implementation designed in this pass — this document's job is confirming the gap
  precisely, not closing it.
- No assumption made about what a Client currently sees — flagged as unverified, not guessed at.

## Related documents

`docs/ROLE_NAVIGATION.md` §3 (CQ-30.1, the original finding this confirms with fresh nav-catalog
evidence), `docs/ENTERPRISE_VALUE_CHAIN.md` (CQ-18, real `Deal.customer_id`), `docs/ENTERPRISE_
BUSINESS_NETWORK.md` (CQ-10, real `Company Card`), `docs/LOGIN_USER_FLOW.md` (CQ-30.1, the
Registration/Invitation gap a Client's first entry would depend on).
