# VerticalRegistry — singleton registry for platform verticals.

from __future__ import annotations

import logging
from typing import Type

from platform_sdk.base_vertical import PlatformVertical
from platform_sdk.exceptions import VerticalAlreadyRegisteredError, VerticalNotFoundError

logger = logging.getLogger(__name__)


class VerticalRegistry:
    _instance: VerticalRegistry | None = None

    def __new__(cls) -> VerticalRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._verticals = {}
            cls._instance._built = {}
        return cls._instance

    def register(self, vertical_cls: Type[PlatformVertical]) -> None:
        code = vertical_cls.vertical_code.strip().lower()
        if code in self._verticals:
            raise VerticalAlreadyRegisteredError(code)
        self._verticals[code] = vertical_cls
        logger.info(
            "vertical_registered code=%s workflow=%s strategy=%s",
            code,
            vertical_cls.workflow_name,
            vertical_cls.manager_strategy,
        )

    def get(self, code: str) -> Type[PlatformVertical]:
        key = code.strip().lower()
        if key not in self._verticals:
            raise VerticalNotFoundError(key)
        return self._verticals[key]

    def get_built(self, code: str):
        key = code.strip().lower()
        if key not in self._built:
            raise VerticalNotFoundError(key)
        return self._built[key]

    def set_built(self, code: str, instance: PlatformVertical) -> None:
        self._built[code.strip().lower()] = instance

    def list(self) -> list[dict[str, str]]:
        return [
            {
                "code": code,
                "workflow_name": cls.workflow_name,
                "manager_strategy": cls.manager_strategy,
            }
            for code, cls in sorted(self._verticals.items())
        ]

    def list_codes(self) -> list[str]:
        return sorted(self._verticals.keys())

    def remove(self, code: str) -> None:
        key = code.strip().lower()
        self._verticals.pop(key, None)
        self._built.pop(key, None)
        logger.info("vertical_removed code=%s", key)

    def clear(self) -> None:
        self._verticals.clear()
        self._built.clear()

    @classmethod
    def reset_singleton(cls) -> None:
        cls._instance = None
        import platform_sdk.vertical_registry as mod

        mod.vertical_registry = VerticalRegistry()


vertical_registry = VerticalRegistry()
