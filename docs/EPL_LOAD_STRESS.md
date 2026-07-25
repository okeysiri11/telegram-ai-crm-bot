# EPL — Load, Stress, Spike & Soak

**Sprint:** 25.2 · **API:** `/api/enterprise-epl/v1`

## Load levels

10 · 50 · 100 · 250 · 500 · 1000 · 5000 users

Metrics: Response Time · Throughput · Error Rate · CPU · RAM · Database · Network

## Stress

Ramp until failure; capture API / DB / queues / AI Hub / Event Bus limits and degradation point.

## Spike

Example pattern: 100 → 1000 → 5000 → 100; measure recovery.

## Soak

1h · 6h · 12h · 24h — memory leaks, error accumulation, degradation, connection stability.
