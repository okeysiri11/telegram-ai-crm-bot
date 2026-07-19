# Migration-safe model registration — imports only database/models/* modules.

from __future__ import annotations

import importlib
from pathlib import Path

_SKIP = frozenset({"__init__", "mixins", "registry"})


_PRIORITY_MODULES = (
    "database.models.user_role",
    "database.models.role",
    "database.models.role_permission",
    "database.models.users",
)


def load_all_models() -> list[str]:
    """Import every ORM model module so tables register on Base.metadata."""
    models_dir = Path(__file__).resolve().parent / "models"
    loaded: list[str] = []

    for module_name in _PRIORITY_MODULES:
        importlib.import_module(module_name)
        loaded.append(module_name)

    for path in sorted(models_dir.glob("*.py")):
        stem = path.stem
        if stem.startswith("_") or stem in _SKIP:
            continue
        module_name = f"database.models.{stem}"
        if module_name in loaded:
            continue
        importlib.import_module(module_name)
        loaded.append(module_name)

    return loaded
