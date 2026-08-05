# Sprint CQ-30.8 — Production Gaps

**Scope:** Production Studio readiness (§6 of the brief) + general infrastructure production readiness
(§7). Documentation only, `src` not modified.

## Part A — Production Studio readiness

Restated and extended from `docs/TECH_DEBT.md` TD-45/TD-46 and `docs/PRODUCTION_STUDIO_UX.md`
(CQ-30.1): a real 17-studio UI shell exists (`productionCatalog.ts`), with **no real generation
backend behind any studio** and **no consent-record infrastructure** for avatar/voice-likeness.

| Capability | Readiness | Problem | Evidence | Priority |
|---|---|---|---|---|
| Image generation | UI only | No real image-generation provider wired | Real `image` studio card, no backend (`TD-45`) | P1 (before enabling) |
| Video generation | UI only | Same | Real `video` studio card, no backend | P1 |
| Voice | UI only, **highest risk** | No backend **and** no consent gate for voice-likeness | Real `voice` studio card, `TD-46`'s consent-gate finding applies most directly here | P0 (before enabling) |
| Documents | Partial-real | Real document storage exists (`docs/EBN_VERIFIED_DOCUMENTS.md`, CQ-10); real concurrent-editing does not | Restated, not re-derived | P2 |
| Prompt templates | UI real | Real `prompt` studio (Prompt Studio), correctly distinguished from AI Builder Studio's separate library (`docs/AI_PRODUCTION_CENTER_BIBLE.md`'s own non-duplication note) | Real | None — working as intended |
| AI agents | Partial-real | Real agent-assignment UI state exists; the agent actually performing generation work does not | `docs/AI_PRODUCTION_CENTER_BIBLE.md` §0 | P1 |
| Workflows | Real pipeline, no real execution behind Generation stage | Real 7-stage pipeline (`draft→review→approval→generation→render→publish→archive`); `generation` stage has no real backend to execute | `productionCatalog.ts`'s `PIPELINE_STAGES` | P1 |

**Bottom line for Part A:** every capability the brief asks about is UI-ready and none is
generation-ready. This is not new information (`TD-45`/`TD-46` already established it), but this
review's job is confirming it precisely against the brief's specific seven-item list — done above.

**Recommended Beta stance:** ship Production Studio in Beta as an explicitly-labeled preview (per
`docs/PRODUCTION_STUDIO_UX.md` §3's card-level honesty recommendation, CQ-30.1, and `docs/FIRST_TIME_
USER.md`'s recommendation to badge the sidebar entry too, CQ-30.7) rather than delaying Beta until
real generation exists — the UI has real value for gathering Beta feedback on workflow/UX even before
generation is real, provided it's honestly labeled.

## Part B — Infrastructure production readiness

| Area | Readiness | Evidence | Gap |
|---|---|---|---|
| Docker | **Real, mature** | Multi-stage build implied by `docker-compose.prod.yml`'s `build: .` | None found |
| Compose | **Real, mature** | 6 real services, real healthchecks on postgres/redis, real `restart: unless-stopped` | `bot` service itself lacks a healthcheck (`docs/OBSERVABILITY_REVIEW.md` §2) |
| Nginx | **Real, but production-incomplete** | Real `nginx.conf`, confirmed wired into prod compose, ports 80+443 both exposed | **No TLS/SSL configured** — no `server { listen 443 }` block, no `ssl_certificate` directive; the catch-all `location /` still returns a static placeholder string `'Auto CRM Marketplace'` instead of proxying to the real frontend |
| Redis | **Real, mature** | Real healthcheck, `--appendonly yes` (persistence enabled), real `redis_data` volume | None found |
| PostgreSQL | **Real, mature** | Real healthcheck, real `postgres_data` volume, real backup volume mount (`./scripts/backup:/backup`) | None found at the compose level |
| Storage | **Real, multi-backend** | `services/storage/__init__.py` — real Telegram/Local/S3/CDN providers | Which backend Beta will actually use in production not confirmed this pass |
| Backups | **Real infrastructure, one policy violation** | Real `scripts/backup_db.sh`, real `docs/BACKUP_GUIDE.md`, real backup volume in compose | A real SQLite artifact (`backups/backup_2026_07_12_12_55.db`) sits in the backup directory despite `POSTGRES_ONLY=true` policy |
| Monitoring | **Real** | Real Prometheus + Grafana (`docs/OBSERVABILITY_REVIEW.md` §1) | Default Grafana admin password fallback (`docs/SECURITY_REVIEW.md` §9) |
| Logging | **Partial** | Structured log calls confirmed in sampled code | No log aggregation service (`docs/OBSERVABILITY_REVIEW.md` §3) |
| Health checks | **Partial** | Real for postgres/redis | Missing for `bot` itself (`docs/OBSERVABILITY_REVIEW.md` §2) |

## The two concrete infrastructure blockers

1. **Nginx has no real TLS configuration** despite port 443 being exposed — this is the single most
   surprising infrastructure gap this review found, because the port is opened (suggesting HTTPS was
   intended) but the certificate/server-block work was never finished. A Beta customer's browser would
   either fail to connect on 443 or connect insecurely, depending on how the gap manifests in practice.
   - **Priority:** P0. **Effort:** S-M (add a `server { listen 443 ssl; }` block + a real certificate,
     e.g. via Let's Encrypt/Certbot — a well-understood, bounded task).
2. **The nginx catch-all still returns a placeholder string**, not the real frontend — worth confirming
   this is intentional (e.g., the real frontend is served by a different path/service) before Beta,
   since as written it reads as an unfinished config.
   - **Priority:** P0 (verify) — could be a documentation gap in this review rather than a real bug if
     the frontend is genuinely served elsewhere; needs direct confirmation either way.

## Non-goals

- No generation backend implemented for any Production Studio capability.
- No TLS certificate provisioned or nginx config changed — flagged, not fixed, per this sprint's
  documentation-only constraint.

## Related documents

`docs/TECH_DEBT.md` (TD-45, TD-46, TD-30), `docs/PRODUCTION_STUDIO_UX.md` (CQ-30.1), `nginx.conf`/
`docker-compose.prod.yml` (real), `docs/OBSERVABILITY_REVIEW.md`/`docs/SECURITY_REVIEW.md` §9 (CQ-30.8
siblings).
