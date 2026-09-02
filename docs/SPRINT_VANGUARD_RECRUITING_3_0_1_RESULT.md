# Sprint Vanguard Recruiting 3.0.1 — production deploy + E2E

**Date:** 2026-09-02  
**Production:** `https://ados-web.onrender.com`  
**Production SHA:** `02ed1cc9338e4b9b360597f42e45fd2120cd5137`

## Deploy

`d2532d02` (2.10 identity) was on `origin/develop` but production stayed on `df9569df` (2.8) because Production Gate was red (`checksPass`).

Gate failures (also present on 2.8/2.9):

1. `test_duplicate_application_is_idempotent` expected HTTP 200 for two site posts without `Idempotency-Key`. Unique `VG-*` references made each post a new lead (correct for 2.10). Test now uses `Idempotency-Key` for retries; independent posts remain two leads.
2. Playwright E2E showed empty Vanguard leads: Vite local Owner JWT (`iss=ados-enterprise-local`) is unsigned. Production still rejects it (`ALLOW_HEADER_AUTH=false`). DEV/header-auth now accepts that local token so CI E2E can read `ados` leads.

After `02ed1cc9`: Production Gate **success**, Render `/liveness` revision matches.

## Production E2E (this SHA)

Dedicated identity `e2e.phase301` (not the real timofii pipeline):

- assign `recruiter.owner` → persists  
- assign vacancy **дронщик** → persists  
- qualify → `qualified` persists  
- convert → one candidate  
- second lead, same person, formatted phone/email → still a separate lead  
- convert #2 → HTTP 200 `identity_linked`, **same candidate**, **two applications**, UTM/`external_id` kept  
- pipeline: one card; QUALIFIED → INTERVIEW → APPROVED → HIRED persists; terminal HIRED  

Historical **timofii** (email `timofiikarpenchuk@gmail.com`):

- two old candidates remain (`APPROVED` + `QUALIFIED`)  
- a third formatted application linked onto the APPROVED candidate (no third candidate)  
- no merge API — not resolved  

HMAC unsigned → `missing_signature`; bad HMAC → `bad_signature`. JWT missing/forged → 401. Owner `demo-corp` still reads `ados` Vanguard rows.
