from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"



import random


class MonteCarloSimulation:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def run(
        self,
        *,
        scenario_id: str | None = None,
        iterations: int = 100,
        mean: float = 100.0,
        stdev: float = 15.0,
        seed: int = 42,
    ) -> dict[str, Any]:
        if iterations < 10 or iterations > 10000:
            raise ValidationError("iterations must be between 10 and 10000")
        rng = random.Random(seed)
        samples = [rng.gauss(mean, stdev) for _ in range(iterations)]
        samples_sorted = sorted(samples)
        p10 = samples_sorted[int(iterations * 0.1)]
        p50 = samples_sorted[int(iterations * 0.5)]
        p90 = samples_sorted[int(iterations * 0.9)]
        mid = _id("esi_mc")
        return self.store.esi_monte_carlo.save(
            mid,
            {
                "simulation_id": mid,
                "scenario_id": scenario_id,
                "iterations": iterations,
                "mean": round(sum(samples) / len(samples), 2),
                "stdev": stdev,
                "p10": round(p10, 2),
                "p50": round(p50, 2),
                "p90": round(p90, 2),
                "min": round(min(samples), 2),
                "max": round(max(samples), 2),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"monte_carlo_runs": len(self.store.esi_monte_carlo.list_all())}
