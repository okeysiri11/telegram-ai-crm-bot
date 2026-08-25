"""Register Casino play-money routes under /api/casino/v1."""

from __future__ import annotations

from aiohttp import web

from applications.casino.api import handlers
from applications.casino.api.middleware import casino_auth_middleware, casino_error_middleware
from applications.casino.config import DEFAULT_CONFIG


def register_casino_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    app.middlewares.append(casino_error_middleware)
    app.middlewares.append(casino_auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_get(f"{prefix}/lobby", handlers.lobby_handler)
    app.router.add_get(f"{prefix}/venues", handlers.venues_handler)
    app.router.add_get(f"{prefix}/venues/{{venue_id}}", handlers.venue_handler)
    app.router.add_get(f"{prefix}/wallet", handlers.wallet_handler)
    app.router.add_get(f"{prefix}/ledger", handlers.ledger_handler)
    app.router.add_post(f"{prefix}/venues/{{venue_id}}/roulette/rounds", handlers.open_round_handler)
    app.router.add_get(f"{prefix}/roulette/rounds/{{round_id}}", handlers.get_round_handler)
    app.router.add_post(f"{prefix}/roulette/rounds/{{round_id}}/bets", handlers.place_bet_handler)
    app.router.add_post(f"{prefix}/roulette/rounds/{{round_id}}/spin", handlers.spin_handler)
    app.router.add_post(f"{prefix}/venues/{{venue_id}}/rooms/join", handlers.join_room_handler)
    app.router.add_post(f"{prefix}/venues/{{venue_id}}/rooms/leave", handlers.leave_room_handler)
    app.router.add_get(f"{prefix}/venues/{{venue_id}}/rooms", handlers.room_handler)
