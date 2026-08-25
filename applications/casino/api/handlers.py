"""Casino HTTP handlers — play-money reads and gated mutations."""

from __future__ import annotations

from aiohttp import web

from applications.casino.api.middleware import json_response
from applications.casino.engine import casino_engine
from applications.casino.exceptions import AuthenticationError, ValidationError
from applications.casino.tenant import player_id_from_principal, tenant_from_request, bind_casino_tenant


def _player_id(request: web.Request) -> str:
    principal = request.get("principal")
    if not isinstance(principal, dict) or not principal.get("authenticated"):
        raise AuthenticationError("Authentication required")
    return player_id_from_principal(principal, fallback="player")


def _bind(request: web.Request) -> None:
    bind_casino_tenant(tenant_from_request(request))


async def health_handler(request: web.Request) -> web.Response:
    _bind(request)
    return json_response(casino_engine.health())


async def lobby_handler(request: web.Request) -> web.Response:
    _bind(request)
    return json_response(await casino_engine.lobby())


async def venues_handler(request: web.Request) -> web.Response:
    _bind(request)
    q = request.query.get("q") or ""
    if q:
        return json_response({"items": await casino_engine.search_venues(q)})
    return json_response({"items": await casino_engine.list_venues()})


async def venue_handler(request: web.Request) -> web.Response:
    _bind(request)
    return json_response(await casino_engine.get_venue(request.match_info["venue_id"]))


async def wallet_handler(request: web.Request) -> web.Response:
    _bind(request)
    return json_response(await casino_engine.wallet(_player_id(request)))


async def ledger_handler(request: web.Request) -> web.Response:
    _bind(request)
    return json_response(await casino_engine.ledger(_player_id(request)))


async def open_round_handler(request: web.Request) -> web.Response:
    _bind(request)
    _player_id(request)
    return json_response(await casino_engine.open_round(request.match_info["venue_id"]), status=201)


async def get_round_handler(request: web.Request) -> web.Response:
    _bind(request)
    return json_response(await casino_engine.get_round(request.match_info["round_id"]))


async def place_bet_handler(request: web.Request) -> web.Response:
    _bind(request)
    player_id = _player_id(request)
    data = await request.json()
    if "result_number" in data or "winning_number" in data:
        raise ValidationError("client cannot supply roulette result")
    bet = await casino_engine.place_bet(
        player_id=player_id,
        round_id=request.match_info["round_id"],
        bet_type=str(data.get("bet_type") or ""),
        amount_chips=int(data.get("amount_chips") or 0),
        numbers=data.get("numbers"),
        idempotency_key=str(data.get("idempotency_key") or ""),
    )
    return json_response(bet, status=201)


async def spin_handler(request: web.Request) -> web.Response:
    _bind(request)
    _player_id(request)
    if request.can_read_body:
        raw = await request.read()
        if raw:
            import json

            data = json.loads(raw.decode("utf-8") or "{}")
            if isinstance(data, dict) and ("result_number" in data or "winning_number" in data):
                raise ValidationError("client cannot supply roulette result")
    return json_response(await casino_engine.spin(request.match_info["round_id"]))


async def join_room_handler(request: web.Request) -> web.Response:
    _bind(request)
    return json_response(await casino_engine.join_room(request.match_info["venue_id"], _player_id(request)))


async def leave_room_handler(request: web.Request) -> web.Response:
    _bind(request)
    return json_response(await casino_engine.leave_room(request.match_info["venue_id"], _player_id(request)))


async def room_handler(request: web.Request) -> web.Response:
    _bind(request)
    return json_response(await casino_engine.room(request.match_info["venue_id"]))
