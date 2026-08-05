"""Client visibility — where modules and menus appear."""

from __future__ import annotations

from enum import Enum


class ClientId(str, Enum):
    WEB = "web"
    TELEGRAM = "telegram"
    DESKTOP = "desktop"
    MOBILE = "mobile"
    API = "api"
    VOICE = "voice"
    AI = "ai"


ALL_CLIENTS: tuple[str, ...] = tuple(c.value for c in ClientId)

# Default: visible on interactive UI clients
DEFAULT_UI_CLIENTS: tuple[str, ...] = (
    ClientId.WEB.value,
    ClientId.TELEGRAM.value,
    ClientId.DESKTOP.value,
    ClientId.MOBILE.value,
)


def normalize_clients(raw: list[str] | tuple[str, ...] | None) -> list[str]:
    if not raw:
        return list(DEFAULT_UI_CLIENTS)
    out: list[str] = []
    for c in raw:
        v = str(c).strip().lower()
        if v in ALL_CLIENTS and v not in out:
            out.append(v)
    return out or list(DEFAULT_UI_CLIENTS)


def visible_on(clients: list[str] | tuple[str, ...] | None, client: str) -> bool:
    return str(client).strip().lower() in normalize_clients(clients)
