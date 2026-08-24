# SPRINT 50.1R RESULT — Localhost recovery + Crypto stack boot

## Root cause

Frontend Vite crashed on a **syntax error** introduced in Sprint 50.1 UI patching:

`CryptoOtcDeskPage.tsx` had duplicated declarations:

- `const pairsPanel  const pairsPanel = (`
- `const specialistsPanel  const specialistsPanel = (`

Vite logged `PARSE_ERROR` / `Missing initializer in const declaration`, then exited. Safari showed the start page because **nothing listened on :5180** (connection refused). Backend `:8080` remained healthy the whole time. Stale `/tmp/ados_web_50_1.pid` pointed at a dead process.

## Fixed

- `src/web/workspace/crypto/CryptoOtcDeskPage.tsx` — removed duplicated `const` lines
- `scripts/run_fx_intel_stack.sh` — idempotent start, `--host 127.0.0.1`, stdin detach, HTTP wait, listener PID files
- `scripts/stop_fx_intel_stack.sh` — kill tree; only stop recognized stack listeners

## Final verified HTTP (this session)

| Check | Status |
|-------|--------|
| `http://127.0.0.1:8080/health` | 200 |
| `http://127.0.0.1:8080/api/crypto-mi/v1/fx-intel/health` | 200 |
| EUR/USD quote | connected |
| DXY quote | connected |
| news / macro / history | 200 |
| `http://127.0.0.1:5180/` | 200 |
| `http://127.0.0.1:5180/login` | 200 |
| `http://127.0.0.1:5180/workspace/crypto` | 200 |
| `http://localhost:5180/` | 200 |

Services left **RUNNING**.
