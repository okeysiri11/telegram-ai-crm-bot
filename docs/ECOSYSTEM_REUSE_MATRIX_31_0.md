# Ecosystem Reuse Matrix — Sprint 31.0

Measured by `computeReusePercentage()` — Automotive · Beauty · Cafe.

| Dimension | Auto | Beauty | Cafe | Shared |
|-----------|:----:|:------:|:----:|:------:|
| authentication … shared_ai (16 rows) | ✓ | ✓ | ✓ | ✓ |
| shared_permissions | ✓ | ✓ | ✓ | ✓ |
| shared_commerce (ECO) | — | ✓ | ✓ | ✓ (Beauty+Cafe) |

## Percentages

- **Platform reuse: 100%** (18/18 shared rows per audit rules)
- **Cross-ecosystem (all three): ~94.4%** (17/18 — commerce intentionally Beauty+Cafe)

## Reusable patterns

See `CROSS_ECOSYSTEM_PATTERNS` in `ecosystem-template/index.ts`.
