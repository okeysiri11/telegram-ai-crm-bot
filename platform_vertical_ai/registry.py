"""Vertical registry — discover and resolve industry AI configs."""

from __future__ import annotations

from platform_vertical_ai.configs import FRAMEWORK_VERTICAL_IDS, VERTICAL_CONFIGS
from platform_vertical_ai.models import VerticalConfig


class VerticalRegistry:
    def __init__(self, configs: dict[str, VerticalConfig] | None = None) -> None:
        self._configs = dict(configs or VERTICAL_CONFIGS)

    def get(self, vertical_id: str) -> VerticalConfig | None:
        return self._configs.get(vertical_id)

    def require(self, vertical_id: str) -> VerticalConfig:
        cfg = self.get(vertical_id)
        if not cfg:
            raise KeyError(f"Unknown vertical: {vertical_id}")
        return cfg

    def list_ids(self) -> list[str]:
        return list(self._configs.keys())

    def list_all(self) -> list[VerticalConfig]:
        return list(self._configs.values())

    def complete_verticals(self) -> list[VerticalConfig]:
        return [c for c in self._configs.values() if c.complete]

    def register(self, config: VerticalConfig) -> None:
        """Add or replace a vertical by configuration only — no code copy."""
        self._configs[config.id] = config

    def public_catalog(self) -> list[dict]:
        return [c.to_public_dict() for c in self._configs.values()]


vertical_registry = VerticalRegistry()

__all__ = ["VerticalRegistry", "vertical_registry", "FRAMEWORK_VERTICAL_IDS"]
