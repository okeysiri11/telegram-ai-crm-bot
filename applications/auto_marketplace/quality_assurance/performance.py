# Performance benchmarks — API, search, CRM, AI, dashboard, portal.

from __future__ import annotations

import time

from applications.auto_marketplace.crm.models import CRMLead, CustomerProfile, LeadSource
from applications.auto_marketplace.release.models import PerformanceBenchmark


class PerformanceBenchmarks:
    THRESHOLDS = {
        "api_health": 50.0,
        "search": 100.0,
        "crm_lead": 150.0,
        "ai_dispatch": 200.0,
        "dashboard": 150.0,
        "portal_search": 150.0,
    }

    async def run_all(self, *, iterations: int = 10) -> list[PerformanceBenchmark]:
        return [
            await self._bench("api_health", iterations, self._api_health),
            await self._bench("search", iterations, self._search),
            await self._bench("crm_lead", iterations, self._crm_lead),
            await self._bench("ai_dispatch", iterations, self._ai_dispatch),
            await self._bench("dashboard", iterations, self._dashboard),
            await self._bench("portal_search", iterations, self._portal_search),
        ]

    async def _bench(self, name: str, iterations: int, fn) -> PerformanceBenchmark:
        times: list[float] = []
        for _ in range(iterations):
            start = time.perf_counter()
            await fn()
            times.append((time.perf_counter() - start) * 1000)
        times.sort()
        p95_idx = min(len(times) - 1, int(len(times) * 0.95))
        threshold = self.THRESHOLDS.get(name, 100.0)
        avg = sum(times) / len(times)
        return PerformanceBenchmark(
            name=name,
            operations=iterations,
            total_ms=sum(times),
            avg_ms=avg,
            p95_ms=times[p95_idx],
            threshold_ms=threshold,
            passed=times[p95_idx] <= threshold,
        )

    @staticmethod
    async def _api_health() -> None:
        from applications.auto_marketplace.application import auto_marketplace

        auto_marketplace.health()

    @staticmethod
    async def _search() -> None:
        from applications.auto_marketplace.application import auto_marketplace

        await auto_marketplace.portal_engine.customer.search_vehicles({"limit": 5})

    @staticmethod
    async def _crm_lead() -> None:
        from applications.auto_marketplace.application import auto_marketplace

        profile = CustomerProfile(email=f"perf-{time.time()}@test.com")
        auto_marketplace.store.customer_profiles.save(profile.customer_id, profile)
        await auto_marketplace.crm_engine.leads.create(
            CRMLead(customer_id=profile.customer_id, source=LeadSource.WEB), profile
        )

    @staticmethod
    async def _ai_dispatch() -> None:
        from applications.auto_marketplace.application import auto_marketplace

        await auto_marketplace.ai_sales_engine.dispatch_agent("customer_assistant", {"message": "perf test"})

    @staticmethod
    async def _dashboard() -> None:
        from applications.auto_marketplace.application import auto_marketplace

        await auto_marketplace.bi_engine.dashboard.get_dashboard("owner")

    @staticmethod
    async def _portal_search() -> None:
        from applications.auto_marketplace.application import auto_marketplace

        auto_marketplace.portal_engine.public.search(limit=5)


performance_benchmarks = PerformanceBenchmarks()
