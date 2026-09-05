# Sprint Vanguard Recruiting 3.2 / 3.2.1 — production E2E + deploy closure

**Date:** 2026-09-05  
**Production:** `https://ados-web.onrender.com`  
**Final status:** **FULL PRODUCTION E2E PASS**

No auth bypass was added. HMAC was not weakened. Provider APIs were not connected or mocked as connected. Historical E2E rows were not deleted.

## 1. Git state before 3.2.1

| Location | SHA | Notes |
|---|---|---|
| `origin/develop` | `5e57afcb` | Pre-ads TEST marker + TEST/PROD column. Gate **failed**. |
| Local `HEAD` | `deb5c56a` | 3.2 RESULT + URL-quote of OAuth state (not the real flake). |
| Render `/liveness` | `d7a56414` | Last green gate (3.1 docs). `checksPass` blocked `5e57afcb`. |

Unrelated dirty files (not committed): `BusinessCabinetShell.tsx`, `docs/SPRINT_50_13_RESULT.md`, untracked FX deploy notes.

`deb5c56a` was **safe** (test URL-encoding + docs) but **not sufficient**. The gate failure was HMAC framing, not query quoting.

## 2. Why `5e57afcb` did not reach Render

`autoDeployTrigger=checksPass`. Production Gate run `33953596635` on `5e57afcb`:

- `web-gate` success
- `vanguard-e2e` success
- `backend-gate` **failure** on Recruiting 1.9  
  `test_oauth_callback_with_injected_exchange` → `AUTH_ERROR` / «OAuth state недействителен.»

Root cause: `encode_state` joined `raw || b"." || hmac_digest`. A SHA-256 digest contains `0x2e` (~12% of states). `rsplit(b".", 1)` then verified the wrong slice. Reproduced locally: 31/200 round-trips failed even when the query string was unchanged. Quoting the state did not fix it.

## 3. Deployment-gate fix (3.2.1)

`eb7fa140` — prefix the 32-byte HMAC, then the JSON payload. Decode tries the new frame first, then the legacy `raw||.||sig` frame when the digest has no `0x2e` (in-flight 10-minute states). HMAC algorithm, keys, JWT, tenant, and ingest auth are unchanged.

Production Gate also now runs `test_sprint_recruiting_3_1_pipeline` (backend + vitest).

## 4. Tests run locally

| Suite | Result |
|---|---|
| Recruiting pytest (1.0–1.9, ingest, hardening, ads, infra, tracking, email, WhatsApp mocked, 2.8, 2.10, 3.0.2, 3.1) | **181 passed**, 3 skipped |
| Recruiting/Vanguard vitest including 3.1 | **13 files / 44 tests** passed |
| `npx vite build` (`src/web`) | **PASS** |
| Security + production health | **53 passed** |
| Playwright Vanguard E2E (this Mac) | not run (Playwright unsupported on mac13) |
| GitHub Production Gate `eb7fa140` | **backend-gate / web-gate / vanguard-e2e success** |
| Production Foundation `eb7fa140` | **success** |

Invariants checked in those suites / live smoke: unsigned ingest 401 `missing_signature`; TEST excluded from production analytics; TEST rows remain in CRM lists; interview schedule idempotent in 3.1 tests; Telegram frozen; Meta/Google disconnected; WhatsApp NOT_CONFIGURED.

## 5. Deployment

Pushed `deb5c56a` + `eb7fa140` to `origin/develop`.

| Check | Result |
|---|---|
| `GET /liveness` revision | `eb7fa14045805dbfe2dcb791d0a59de680db66c1` |
| Includes `5e57afcb` pre-ads markers | yes (ancestor) |
| `runtime` | production |
| Recruiting `GET /health` `production` | `true` |
| `memory_fallback_allowed` | `false` |
| `/workspace/recruiting` | HTTP 200 |

## 6. Human browser hard reload — **HUMAN PASS**

Owner observed after production reload:

- Pre Ads Test still present
- Candidate still in the funnel
- Expected terminal stage **HIRED / Нанят**
- Recruiter `recruiter.ira`
- Application/lead data, source `vanguard-global`, TEST marker
- country EE, program logistics, project vanguard, language en, age 28
- motivation contains `Sprint 3.2 pre-ads TEST`
- Data rehydrated after hard reload

## 7. Post-deploy API smoke (no new applicant)

Authenticated via already-deployed `POST /api/enterprise-demo-auth/v1/login` (owner). Token not printed.

| Check | Result |
|---|---|
| Unsigned `POST /vanguard/leads` | **401 `missing_signature`** |
| Lead `476430f9-…` | `traffic_class=TEST`, `source=vanguard-global`, assignee `recruiter.ira`, UTMs intact, `status=converted` |
| Candidate `1d85e804-…` | TEST, assignee `recruiter.ira`, one application, `durable=true`, `storage=postgres` |
| Application | EE / logistics / vanguard / en / 28 / TEST motivation; Instagram UTMs + landing + referrer |
| Analytics funnel leads/qualified/interviews/approved/hired | **0 / 0 / 0 / 0 / 0** |
| `excluded_test_leads` / `excluded_test_candidates` | **8 / 5** |
| Ads overview leads/hires / `fake_data` | **0 / 0 / false** |
| Ads `source_analytics` | empty |
| Ads providers meta/google/tiktok | `not_connected` |
| Telegram | `frozen=true`, `DISABLED` |
| WhatsApp | `NOT_CONFIGURED` / `WAITING_PROVIDER` |

**Current card stage is INTERVIEW**, not HIRED. History still contains the full 3.2 path through **APPROVED → HIRED** (07:53:23Z). A later `pipeline_moved` **HIRED → INTERVIEW** at **08:01:41Z** (during the human browser session; likely the interview control). That subsequent move does not erase the HIRED proof. The row was not moved back automatically.

## 8. Remaining external blockers

- Meta Ads / Google Ads / TikTok Ads: NOT_CONFIGURED / not_connected
- WhatsApp: NOT_CONFIGURED / WAITING_PROVIDER
- Telegram: frozen / DISABLED
- Paid-ad spend path: **BLOCKED** until real provider credentials exist

## 9. Pre-Ads readiness

CRM path **READY**. Ads APIs **BLOCKED**. **READY_FOR_ADS_SPEND = NO**.

| Component | Status |
|---|---|
| Tracked Vanguard URL + UTM | READY |
| Landing / apply / HMAC ingest / unsigned reject | READY |
| Lead → Candidate → Application | READY |
| Recruiter / qualify / interview / hire | READY |
| Postgres persist + API reload | READY |
| Browser hard reload | **HUMAN PASS** |
| TEST excluded from production/ads metrics | READY |
| Meta / Google / WhatsApp / Telegram | BLOCKED |

## 10. Architectural decisions

- Live apply used the real Vercel signing path.
- TEST isolation uses 3.1 `e2e-` / `traffic_class` plus `5e57afcb` campaign markers (`vanguard_pre_ads_test`, `pre_ads_test`).
- Historical e2e rows identified, not deleted.
- OAuth state framing fixed without changing HMAC keys or auth semantics.
- `deb5c56a` quote kept as URL hygiene; it is not the gate fix.

---

## Sprint 3.3 — proposed backlog (DO NOT IMPLEMENT HERE)

**Title:** Vanguard Advertising Control Center  
**Rule:** do not fake provider metrics; do not connect Meta/Google/WhatsApp/Telegram until real credentials exist.

Existing surface to **extend** (do not replace):

- `GET /api/recruiting-ops/v1/ads/control-center`
- `src/web/workspace/recruiting/AdsControlCenterPage.tsx`
- `services/recruiting_ops/ads_control.py`, `attribution.py` (`source_analytics`, `production_cohort`)
- Manual `POST /campaigns` (operator spend allowed; impressions/clicks stay empty until LIVE)

### Goal

Join the already-proven path:

Vanguard site → UTM/campaign → application → lead → candidate → recruiter → interview → approved → hired

to **campaign/source economics** without inventing clicks or spend.

### Calculate (when inputs exist; otherwise `null` + «Нет живых данных»)

impressions, clicks, CTR, spend, CPC, applications, CPL, qualified, interviews, approved, hired, cost per hire, conversion rates.

### Dimensions

campaign_id / utm_campaign / utm_source / utm_medium / utm_content  
Sources: Meta, Facebook, Instagram, Google, TikTok, organic, direct, referral.

### Suggested slices

1. Campaign registry mapped to Vanguard UTMs (manual campaigns already exist).
2. Production-only funnel already in analytics — add per-campaign / per-source table (TEST stays excluded).
3. Honest provider cards: WAITING_PROVIDER until credentials; no CONNECTED fake.
4. Operator-entered spend remains REAL; provider impressions/clicks stay unavailable.
5. Cost-per-hire / CPL only when spend + production counts exist.
6. Do not implement live Meta/Google sync in 3.3 unless credentials are provided in that sprint.

Rejected for 3.3 unless explicitly requested: inventing impressions, marking providers connected, weakening TEST exclusion, new ads database.
