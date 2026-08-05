# Load Test Report — Sprint 37.3

## Method

In-process measured harness (no external locust/k6 dependency in-repo):

| Mode | Implementation | Result |
|------|----------------|--------|
| Load | 25 concurrent AI Runtime sessions (`asyncio.gather`) | **1.83 ms** total, **0.07 ms**/session |
| Stress | Event-loop lag ×80 samples | p95 **&lt; 0.05 ms** |
| Endurance | Permission engine ×400 iterations | **0** errors |
| Concurrency | Same as load + workflow queue drains | PASS |

Synthetic Sprint 21.7/25.2 façades remain for certification APIs but are **not** used as evidence for 37.3.

## Targets vs observed

| Target | Observed | Notes |
|--------|----------|-------|
| Concurrent AI sessions ≥ 20 | **25** | Mocked provider |
| Event-loop lag p95 &lt; 5 ms | **0.048 ms** | PASS |
| Workflow queue sustained ops | ~**3.8k ops/s** | In-process |
| Event bus publish | ~**7.6k ops/s** | In-process wait=True |
| Error rate | **0** on core benches | PASS |

## Gaps (external load)

| Pri | Item | Effort |
|-----|------|--------|
| P2 | k6/locust scripts against `/health`, management JWT, AI routes | 2d |
| P2 | WebSocket fan-out soak (100–1k clients) | 2d |
| P2 | Multi-hour soak with memory RSS trending | 1d |

## Verdict

**Load / stress / endurance / concurrency slices: PASS** for control-plane and in-process runtimes. Staging HTTP soak remains P2 before GA traffic claims.
