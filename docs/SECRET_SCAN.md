# Secret Scan — Sprint 37.2

## Method

1. `platform_security.secret_policy.scan_repo_for_insecure_defaults`
2. `validate_runtime_secrets` (production/staging fail-closed)
3. Repository ripgrep for placeholder / test passwords
4. ConfigurationCenter validation wired to secret_policy (37.2)

## Results

| Scan | Result |
|------|--------|
| Repo insecure-default scan | **PASSED** (2 non-critical info/warn) |
| Live production env with placeholders | **FAIL-CLOSED** (startup `fail_fast`) |
| Hardcoded production credentials in source | **None found** |
| Test fixtures using passwords | Expected (tests only) |

### Static findings (accepted)

| Severity | Code | Message |
|----------|------|---------|
| info | N8N_KEY_OK | N8N key must be explicit env |
| warn | SETTINGS_DEFAULT_PLACEHOLDER | Pydantic defaults still list placeholders — rejected at prod validate |

## Remediations in 37.2

- Staging treated as production for secret gates.
- CRM bootstrap key separated (`CRM_BOOTSTRAP_API_KEY`).
- Skills signing prefers `SKILLS_SIGNING_SECRET`.
- `ALLOW_HEADER_AUTH` cannot remain enabled in prod/staging.

## Remaining

| Pri | Item | Effort |
|-----|------|--------|
| P1 | Rotate any historically shared JWT/CRM bootstrap secrets in deployed envs | 0.5d ops |
| P2 | Remove placeholder strings from Pydantic Field defaults (use empty) | 0.5d |
| P3 | Add gitleaks + pip-audit to CI | 1d |

## Verdict

**No exposed production secrets in repository.** Enterprise secret posture **READY** with fail-closed startup.
