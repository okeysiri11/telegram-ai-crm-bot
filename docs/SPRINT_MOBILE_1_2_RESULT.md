# Sprint MOBILE 1.2 — Operational mobile (AUTO / AGRO)

Home chrome from MOBILE 1.1 is unchanged. This sprint makes operational screens, uploads, search, settings, session, and role gates work on the phone.

## What shipped

1. **Ops cabinet:** loading skeleton, retry, offline copy, tappable cards, thumbnails, «Показать ещё» on mobile. Duplicate «Разделы» toggle hidden under 768px (workspace drawer already has nav).
2. **AUTO:** vehicle cards open details; `+ Автомобиль` deep-links to `?view=vehicles&action=create`; photo upload shows progress; lazy thumbs.
3. **RBAC (server is source of truth):** `auto_customs` role in `services/auto_ops/rbac.py`. Accountant has no `edit` (cannot change logistics). Manager/forwarder/customs have no `finance`. UI hides finance/expenses/reports and disables logistics mutations to match, but 403 still comes from the API.
4. **Session / deep links:** login `from` keeps `pathname + search + hash` (`/workspace/auto?vehicle=` survives auth).
5. **Performance:** Auto / Agro / Beauty / Cafe / Legal / Crypto workspace pages are lazy-loaded.
6. **Search:** header ⌕ sheet; Auto VIN search hits `/api/auto-ops/v1/search`, otherwise `/search`.
7. **Settings:** mobile index lists only authorized sections (Профиль … AUTO / AGRO / источники).
8. **API:** 20s timeout; relative `/api` prefixes (public Cloudflare compatible).

## Architectural decisions

- Extend existing `shell/mobile` + `BusinessCabinetShell` + `auto_ops` RBAC. No new platform package.
- Client nav hiding is UX only; permissions stay in `services/auto_ops/rbac.py`.

## Genuinely unsupported

- Live AIS / automatic container tracking (already documented as manual).
- Company-wide profit for manager/forwarder (correctly denied).
- Desktop God Mode / owner analytics walls on the phone (intentionally not ported).

AUTO 1.9 and MOBILE 1.3 were not started.
