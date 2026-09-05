# Sprint 3.3.2 — Provider Connection UI Crash Fix

**Date:** 2026-09-05  
**Mode:** Production bugfix. No new features. No live OAuth.

## Root cause

«Открыть подключения» on Recruiting → Реклама → Провайдеры was a React Router
`<Link to="/workspace/recruiting/integrations">`. That route is a **separate
`React.lazy` hop** in `src/web/src/App.tsx`:

```ts
import("../workspace/recruiting/ProviderConnectionsPage")
```

Production index (`/assets/index-iORdSZ0_.js` at investigation time) resolved that
to `/assets/ProviderConnectionsPage-BGTQoEAY.js`. A failed dynamic `import()`
surfaces as:

`Importing a module script failed.`

and the **global** Reliability `ErrorBoundary` then replaced the whole Recruiting
view (`This view failed to render`).

A current cold fetch of that hashed chunk returned HTTP 200 / `text/javascript`.
The user-facing failure class is still a **stale or broken lazy chunk** after
deploy (old index → old hash → 404/HTML), plus the link dropped `?embed=1`
(Desktop windows load Ads as `embed=1`).

## Failing module / chunk

- Route: `/workspace/recruiting/integrations`
- Component: `ProviderConnectionsPage` (named export)
- Lazy path: `src/web/workspace/recruiting/ProviderConnectionsPage.tsx`
- Observed production chunk: `/assets/ProviderConnectionsPage-BGTQoEAY.js`
- Importer: `/assets/index-iORdSZ0_.js`

There is no separate `ProviderConnectionWizard` / `ProviderOAuthWizard` module.
The wizard is the connections UI (Ads providers tab + integrations page).

## Fix

- Ads «Открыть подключения» opens an **in-place dialog** on the already-loaded
  Ads chunk. No navigation. No extra lazy hop.
- Missing-app-env copy is shown for Meta / Google / TikTok. OAuth redirect runs
  only when `authorize_url` is present **and** `ok` is true.
- `ProviderConnectionBoundary` keeps load/render failures local (RU fallback +
  «Повторить» / «Обновить страницу»). Global Reliability is not used.
- `/integrations` uses `SafeProviderConnectionsRoute`: lazy import is `catch`ed
  and remounted on retry.
- Recruiting side nav preserves `embed=1`.

Provider honesty is unchanged: Meta / Google / TikTok stay `NOT_CONFIGURED`.
No credentials were invented. No real OAuth.

## Tests

- `src/web/workspace/recruiting/sprint_recruiting_3_3_2.test.tsx` — **5 passed**
  (page render, in-place wizard, missing-config, local fallback, retry remount)
- Recruiting vitest regression (1.0–1.9, 2.10, 3.0.2, 3.1, 3.3 ads/phase2, email, WhatsApp, career) — **passed**
- Recruiting pytest (3.3 ads/phase2, 1.8, 1.9, WhatsApp, 3.1) — **88 passed**
- Production Gate vitest list includes `sprint_recruiting_3_3_2.test.tsx`

## Build

- `npx vite build` (`src/web`) — **PASS** (39.85s)
- Ads wizard lives in `AdsControlCenterPage-*.js` (no extra hop for «Открыть подключения»)
- `/integrations` still lazy-loads `ProviderConnectionsPage-*.js`, wrapped by `SafeProviderConnectionsRoute`
- `tsc -b` remains report-only (pre-existing unrelated vertical debt)

## Architectural decisions

- **In-place wizard over fixing only the lazy URL.** The owner path must not
  depend on a second hashed chunk after a Render deploy.
- **Local boundary, not RouteErrorBoundary.** Sprint requirement: do not dump
  the operator onto the global Reliability screen.
- **Extend Ads / integrations UI.** No new provider system.
