"""Integration: API v1 scaffold routes register."""

def test_register_api_v1_routes():
    from aiohttp import web
    from api.v1 import register_api_v1_routes

    app = web.Application()
    register_api_v1_routes(app)
    paths = {getattr(r.resource, "canonical", None) for r in app.router.routes()}
    assert "/api/v1/leads" in paths
    assert "/api/v1/inventory" in paths
