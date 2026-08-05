# Google Login — Sprint 30.3

**Preferred Beta auth** (extends Sprint 30.1).

## Flow

1. `/login` → «Продолжить через Google»
2. `authStore.loginWithGoogle` → `productionGoogleLogin` (ISAM or demo)
3. Organization set via top-bar / login tenant (`useOrgSelector`)
4. If first-run incomplete → `/onboarding/first-entry`
5. Else → role home (`/owner`, `/dashboards/client`, `/dashboards/dealer`, or `/dashboard`)

## Supports

- Login
- Registration (auto account on first Google login — ISAM)
- Organization join (tenant + org selector)
- First Login Wizard (First Entry)

Docs: also `GOOGLE_AUTH.md` (30.1).
