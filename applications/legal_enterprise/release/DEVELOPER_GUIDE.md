# Developer Guide

## Package layout

`applications/legal_enterprise/<module>/` — additive domain modules  
`applications/legal_enterprise/enterprise_certification/` — Sprint 17.8 certification  
`applications/legal_enterprise/api/` — handlers + `register.py`  
`applications/legal_enterprise/shared/store.py` — append-only buckets  

## Rules

- Do not modify prior Legal domain packages when adding a sprint.
- Wire new modules via store buckets, config, application, API register, and manifest only.
- Add tests under `tests/test_*_17_N.py` and bump prior version asserts.
- Keep frozen: AI OS `3.4.0-alpha`, Enterprise `4.0.0`, Auto `4.2.0`, Agro `4.4.0`, Port `4.6.0`, Crypto `4.8.0`.

## Certification API

See `docs/LEGAL_ENTERPRISE_API.md`.
