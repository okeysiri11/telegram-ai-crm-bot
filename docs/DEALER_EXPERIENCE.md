# Sprint CQ-30.7 — Dealer Experience Review

**Scope:** review Dealer Mode. Documentation only, `src` not modified.

## 1. What's real: same pattern as Client — a switcher entry, no dedicated platform-wide nav

`enterpriseRuNav.ts`'s real `ROLE_SWITCHER_OPTIONS` includes `{ id: "dealer", label: "Дилер", roleIds:
["dealer"] }`. Like Client, no dedicated `DEALER_RU_NAV` array exists in the real catalog. Unlike
Client, Dealer has real, substantial *backend* data — `AutomotiveDealerSource`/`DealerSourceType`
(`database/models/automotive_partner_integration.py`) and real commission tracking
(`DealEngineCommission`) — but this real data is automotive-vertical-scoped, not a platform-wide
concept the general 23-item sidebar has any awareness of.

- **Why it matters:** a Dealer switching into their role today would see either the general internal
  sidebar (inappropriate — a Dealer is not an internal employee and shouldn't see CRM/ERP/Legal/
  Finance) or nothing dealer-specific at all. Neither is confirmed; both are plausible given no
  dedicated nav array exists.
- **Impact:** High for any Beta cohort that includes real automotive dealers specifically — this is the
  vertical with the most real backend readiness (per `docs/ENTERPRISE_SCENARIO_LIBRARY.md`'s Logistics/
  Crypto/IT-adjacent "real" tier, CQ-17) but the least platform-wide UX investment for its own users.
- **Priority:** P1.
- **Complexity:** M — unlike Client (which needs new UX from a real-but-generic data foundation),
  Dealer needs a nav surface pointed at *already-real, already-rich* automotive data (inventory, deal
  pipeline, commission) — the harder design work (what data to show) is largely done; the gap is purely
  navigational.
- **Evidence:** `enterpriseRuNav.ts`'s `ROLE_SWITCHER_OPTIONS`; `automotive_partner_integration.py`
  (real `AutomotiveDealerSource`); `database/models/commission.py`'s real `DealEngineCommission`.

## 2. This is the platform's best-positioned "quick win" persona

Of the three under-specified roles this sprint's siblings review (Client, Dealer, and — per `docs/
ROLE_NAVIGATION.md`, CQ-30.1 — no Production-specific nav array either), Dealer requires the least new
backend investment: real inventory, real deal pipeline (`docs/ENTERPRISE_VALUE_CHAIN.md`'s
recommended-canonical `DealPipelineStageCode`, CQ-30), and real commission data all already exist. A
`DEALER_RU_NAV` array pointed at these three real destinations would close this gap with minimal new
design work relative to Client's genuinely-from-scratch portal need.

## 3. Terminology

Real "Дилер" is a clean, unambiguous Russian term with no collision risk found (unlike Marketplace/
Marketing) — no linguistic finding here, the gap is purely structural.

## Non-goals

- No Dealer navigation array implemented in this pass — this document scopes and prioritizes the gap,
  it does not close it.
- No assumption about what a Dealer currently sees in the app — flagged as unverified, same discipline
  as `docs/CLIENT_EXPERIENCE.md`.

## Related documents

`docs/ROLE_NAVIGATION.md` §3 (CQ-30.1), `docs/ENTERPRISE_VALUE_CHAIN.md` (CQ-18/CQ-30, real
`DealPipelineStageCode`), `docs/CLIENT_EXPERIENCE.md` (CQ-30.7 sibling, the comparable-shaped but
harder gap), `docs/ENTERPRISE_SCENARIO_LIBRARY.md` (CQ-17, automotive vertical's real-tier status).
