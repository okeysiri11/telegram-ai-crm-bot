# Sprint — Owner DEV access reset + zero-friction local login

Local Owner testing without ISAM, Google, or the API. Production authentication is unchanged.

## Architectural decisions

- **Extend `demoAuthProvider`.** Canonical identity remains `owner@ados.demo` / tenant `ados` / `platform_owner`. No new auth provider.
- **DEV-only surface.** `isLocalOwnerLoginEnabled()` requires `!PROD` and `isDemoAuthEnabled()`. `VITE_DEMO_AUTH=true` is still ignored in production builds (runtime + Vite plugin).
- **`returnTo` is any safe internal path.** Open-redirect checks stay (relative path, no `//`, no protocol, login/logout blocked). This preserves casino and workspace deep links.
- **Owner smoke matrix from catalogs.** `ownerAccessRegistry.ts` unions boot, launch, vertical, module, and casino route catalogs. `platform_owner` view-mode allow-all plus `PermissionGuard` owner bypass.

## What shipped

- Login primary CTA: **Войти как Owner**
- Non-blocking status: external auth offline, local Owner mode available
- Email / Google / registration / password recovery collapsed locally
- One-click session: JWT-shaped local token, full permissions, tenant `ados`
- Casino and workspace `returnTo` after Owner click

## Recruiting audit (no implementation)

- No dedicated Recruiting / Vanguard frontend, backend package, DB schema, or marketing route
- City HR building → `/identity/users` (not `/workspace/hr`)
- Search index still lists `/workspace/hr` as a generic module shell
- `ecosystem/workforce/` is a separate workforce engine, not recruiting/ATS

## Intentionally deferred

- Recruiting + Vanguard Lead Acquisition vertical
- Unrelated tsc debt (odessa3d / agro / crypto / hercules)
