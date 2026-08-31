"""Recruiting projects catalog — Vanguard is a project, not a vertical."""

from __future__ import annotations

import os
from typing import Any

from services.recruiting_ops.runtime import is_production_runtime

VANGUARD_PROJECT_KEY = "vanguard"

STATUS_CONNECTED = "CONNECTED"
STATUS_DEGRADED = "DEGRADED"
STATUS_DISCONNECTED = "DISCONNECTED"
STATUS_OFFLINE = "DISCONNECTED"
STATUS_UNKNOWN = "UNKNOWN"
STATUS_NOT_CONFIGURED = "NOT_CONFIGURED"

STATUS_RU = {
    STATUS_CONNECTED: "Подключено",
    STATUS_DEGRADED: "Сбои",
    STATUS_DISCONNECTED: "Отключено",
    STATUS_UNKNOWN: "Нет данных",
    STATUS_NOT_CONFIGURED: "Не настроено",
}

RECRUITING_PROJECTS: tuple[dict[str, Any], ...] = (
    {
        "project_key": VANGUARD_PROJECT_KEY,
        "name": "Vanguard",
        "type": "recruiting_website",
        "type_ru": "Сайт рекрутинга",
        "description_ru": "Сайт Vanguard отправляет заявки в Рекрутинг. Лиды становятся кандидатами.",
    },
)


def _txt(value: Any) -> str:
    return str(value or "").strip()


def project_catalog() -> list[dict[str, Any]]:
    return [dict(item) for item in RECRUITING_PROJECTS]


def get_project(project_key: str) -> dict[str, Any] | None:
    key = _txt(project_key).lower()
    for item in RECRUITING_PROJECTS:
        if item["project_key"] == key:
            return dict(item)
    return None


def resolve_project_key(item: dict[str, Any] | None) -> str:
    if not item:
        return ""
    key = _txt(item.get("project_key")).lower()
    if key:
        return key
    source = _txt(item.get("source")).lower()
    if source == VANGUARD_PROJECT_KEY:
        return VANGUARD_PROJECT_KEY
    return ""


def belongs_to_project(item: dict[str, Any] | None, project_key: str) -> bool:
    key = _txt(project_key).lower()
    if not key or not item:
        return False
    return resolve_project_key(item) == key


def infer_project_key(*, source: str | None = None, project_key: str | None = None) -> str | None:
    explicit = _txt(project_key).lower()
    if explicit:
        return explicit
    src = _txt(source).lower()
    if src == VANGUARD_PROJECT_KEY or src == "vanguard-global" or src.startswith("vanguard-"):
        return VANGUARD_PROJECT_KEY
    return None


def vanguard_website_url() -> str | None:
    """Public website URL from env. Never treat localhost as a production URL."""
    url = (
        os.getenv("VANGUARD_WEBSITE_URL")
        or os.getenv("VANGUARD_PUBLIC_URL")
        or ""
    ).strip()
    if not url:
        return None
    lowered = url.lower()
    local = "localhost" in lowered or "127.0.0.1" in lowered
    if is_production_runtime() and local:
        return None
    return url


UI_STATE = {
    STATUS_CONNECTED: "ONLINE",
    STATUS_DEGRADED: "DEGRADED",
    STATUS_DISCONNECTED: "OFFLINE",
    STATUS_UNKNOWN: "NO DATA",
    STATUS_NOT_CONFIGURED: "NO DATA",
}


def status_payload(code: str, *, reason_ru: str | None = None) -> dict[str, str]:
    raw = code if code in STATUS_RU else STATUS_UNKNOWN
    out = {"code": raw, "label_ru": STATUS_RU[raw], "ui_state": UI_STATE.get(raw, "NO DATA")}
    if reason_ru:
        out["reason_ru"] = reason_ru
    return out
