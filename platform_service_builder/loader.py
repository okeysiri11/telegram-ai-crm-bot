"""Service loader — load service modules without mutating platform core."""

from __future__ import annotations

import importlib
import logging
import sys
from typing import Any

logger = logging.getLogger(__name__)


class ServiceLoader:
    """
    Loads optional service modules by dotted path.
    Never imports or patches platform core packages.
    """

    def __init__(self) -> None:
        self._loaded: dict[str, Any] = {}

    def reset(self) -> None:
        self._loaded.clear()

    def is_loaded(self, service_id: str) -> bool:
        return service_id in self._loaded

    def get(self, service_id: str) -> Any | None:
        return self._loaded.get(service_id)

    def load(
        self,
        service_id: str,
        *,
        module_path: str | None = None,
        entrypoint: str | None = None,
    ) -> dict[str, Any]:
        if not module_path:
            # Virtual service — no Python module; mark as loaded stub
            stub = {"service_id": service_id, "virtual": True, "entrypoint": entrypoint}
            self._loaded[service_id] = stub
            return {"loaded": True, "virtual": True, "module": None, "service_id": service_id}

        try:
            module = importlib.import_module(module_path)
            if entrypoint and hasattr(module, entrypoint):
                target = getattr(module, entrypoint)
                if callable(target) and not isinstance(target, type):
                    # factory / bootstrap callable
                    try:
                        instance = target()
                    except TypeError:
                        instance = target
                else:
                    instance = target
                self._loaded[service_id] = instance
            else:
                self._loaded[service_id] = module
            return {
                "loaded": True,
                "virtual": False,
                "module": module_path,
                "entrypoint": entrypoint,
                "service_id": service_id,
            }
        except Exception as exc:
            logger.warning("service load failed service=%s module=%s err=%s", service_id, module_path, exc)
            raise RuntimeError(f"Failed to load service {service_id}: {exc}") from exc

    def unload(self, service_id: str) -> bool:
        return self._loaded.pop(service_id, None) is not None

    def reload(
        self,
        service_id: str,
        *,
        module_path: str | None = None,
        entrypoint: str | None = None,
    ) -> dict[str, Any]:
        if module_path and module_path in sys.modules:
            mod = sys.modules.get(module_path)
            if mod is not None:
                importlib.reload(mod)
        self.unload(service_id)
        return self.load(service_id, module_path=module_path, entrypoint=entrypoint)


service_loader = ServiceLoader()
