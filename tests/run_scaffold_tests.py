# Minimal test runner for architecture scaffold (no pytest required).

from __future__ import annotations


def main() -> None:
    from container import get_container, reset_container

    reset_container()
    c = get_container()
    assert "storage" in c.registry.registered_names()

    from src.events import LeadCreated

    assert LeadCreated().event_type == "LeadCreated"

    from src.platform.analytics import KpiCalculator

    assert KpiCalculator.conversion_rate(1, 4) == 25.0

    from aiohttp import web
    from api.v1 import register_api_v1_routes

    app = web.Application()
    register_api_v1_routes(app)

    from src.domains import DOMAIN_NAMES

    assert len(DOMAIN_NAMES) == 14
    print("architecture_scaffold_tests: OK")


if __name__ == "__main__":
    main()
