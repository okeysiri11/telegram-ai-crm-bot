# Payload mapper — transform between internal and external formats.

from __future__ import annotations

from typing import Any

from platform_integrations.exceptions import PayloadMappingError


class PayloadMapper:
    _maps: dict[str, dict[str, str]] = {
        "telegram": {"message": "text", "chat_id": "chat_id"},
        "email": {"message": "body", "to": "recipient"},
        "sms": {"message": "body", "to": "phone"},
        "http_rest": {},
        "webhook": {},
    }

    @classmethod
    def to_external(cls, provider: str, payload: dict[str, Any]) -> dict[str, Any]:
        mapping = cls._maps.get(provider, {})
        if not mapping:
            return dict(payload)
        try:
            return {mapping.get(k, k): v for k, v in payload.items()}
        except Exception as exc:
            raise PayloadMappingError(str(exc)) from exc

    @classmethod
    def to_internal(cls, provider: str, payload: dict[str, Any]) -> dict[str, Any]:
        mapping = cls._maps.get(provider, {})
        if not mapping:
            return dict(payload)
        reverse = {v: k for k, v in mapping.items()}
        try:
            return {reverse.get(k, k): v for k, v in payload.items()}
        except Exception as exc:
            raise PayloadMappingError(str(exc)) from exc

    @classmethod
    def register_map(cls, provider: str, field_map: dict[str, str]) -> None:
        cls._maps[provider] = field_map


payload_mapper = PayloadMapper()
