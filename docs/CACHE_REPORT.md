# Cache Report — Sprint 37.3

## Layers

| Layer | Location | Notes |
|-------|----------|-------|
| Platform LRU/TTL | `platform_state.cache` | Entities / events / query TTL 15s |
| Prompt cache | `platform_ai.prompt_runtime` | Local hits/misses |
| Dashboard widgets | `platform_operations.dashboard_service` | Redis + `cache_hit` flags |
| Config | `platform_configuration.config_cache` | Redis get/setex |
| FSM | `fsm_storage.py` | RedisStorage when `REDIS_URL` set |

## Hit ratio (measured)

| Path | Hit rate |
|------|----------|
| platform_cache LRU bench (200 keys, 50 unique) | **0.996** |

Sprint 37.3 wires `enterprise_telemetry.cache_hit_rate()` into snapshot and emits `cache.hit_rate` via `enterprise_metrics`.

## Redis

| Check | Result |
|-------|--------|
| Latency bench | **Skipped** — Redis not reachable on bench host |
| Production requirement | Required when `ENVIRONMENT` in production/staging |

### Recommended prod

```
REDIS_URL=redis://...
REDIS_REQUIRED=true
```

Shared connection pool (single client factory) remains **P1** — multiple `Redis.from_url` call sites exist.

## Verdict

**Redis control path ready; cache hit ratio instrumentation READY.** Live Redis INFO hit-ratio aggregation = P1 (2d).
