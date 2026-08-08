# Auto Russian First

Hard requirement for Auto Telegram (Sprint 46.1).

## Rules

1. Client-facing replies are Russian (UA optional via localization keys).
2. Prefer `t("telegram.auto.*")` for stable strings.
3. Plan IDs stay English (`starter`/`pro`/…) — **labels** are Russian (Старт / Профессиональный / …).
4. CI gate: `services/auto_localization_gate.py::scan_user_facing_strings()`.

## Forbidden client strings (examples)

- Dealer rates not configured…  
- No active tenant context  
- STARTER / PRO / BUSINESS / ENTERPRISE as button labels  
- unlimited channels / AI ecosystem access / custom plan / dedicated support  
- Score / Priority / Dept / Intent  

Brands and model codes (BMW, X5) are allowed.
