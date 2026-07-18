# @deprecated decorator — metadata, warnings, and documentation registry.

from __future__ import annotations

import functools
import inspect
import logging
import warnings
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from platform_legacy.deprecation_manager import DeprecatedApi, deprecation_manager

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


@dataclass(frozen=True, slots=True)
class DeprecationMetadata:
    name: str
    replacement: str
    removal_version: str
    subsystem: str
    deprecated_since: str
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "replacement": self.replacement,
            "removal_version": self.removal_version,
            "subsystem": self.subsystem,
            "deprecated_since": self.deprecated_since,
            "reason": self.reason,
        }


_REGISTRY: dict[str, DeprecationMetadata] = {}


def deprecated(
    *,
    replacement: str,
    removal_version: str = "3.0.0",
    subsystem: str = "legacy",
    deprecated_since: str = "2026-07",
    reason: str = "",
) -> Callable[[F], F]:
    """Mark callable as deprecated; log warning on each use."""

    def decorator(fn: F) -> F:
        qualname = getattr(fn, "__qualname__", fn.__name__)
        module = getattr(fn, "__module__", "")
        api_name = f"{module}.{qualname}" if module else qualname
        meta = DeprecationMetadata(
            name=api_name,
            replacement=replacement,
            removal_version=removal_version,
            subsystem=subsystem,
            deprecated_since=deprecated_since,
            reason=reason,
        )
        _REGISTRY[api_name] = meta
        deprecation_manager.register(
            DeprecatedApi(
                name=api_name,
                subsystem=subsystem,
                replacement=replacement,
                deprecated_since=deprecated_since,
                removal_target=removal_version,
            )
        )

        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                _emit_deprecation_warning(meta)
                return await fn(*args, **kwargs)

            async_wrapper.__deprecated__ = meta  # type: ignore[attr-defined]
            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(fn)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            _emit_deprecation_warning(meta)
            return fn(*args, **kwargs)

        sync_wrapper.__deprecated__ = meta  # type: ignore[attr-defined]
        return sync_wrapper  # type: ignore[return-value]

    return decorator


def _emit_deprecation_warning(meta: DeprecationMetadata) -> None:
    message = (
        f"{meta.name} is deprecated since {meta.deprecated_since} "
        f"and will be removed in v{meta.removal_version}. "
        f"Use {meta.replacement} instead."
    )
    if meta.reason:
        message += f" Reason: {meta.reason}"
    logger.warning("deprecated_api_used %s", meta.name, extra={"deprecation": meta.to_dict()})
    warnings.warn(message, DeprecationWarning, stacklevel=3)
    deprecation_manager.mark_api_used(meta.name)


def list_registered_deprecations() -> list[dict[str, Any]]:
    return [meta.to_dict() for meta in sorted(_REGISTRY.values(), key=lambda m: m.name)]


def generate_deprecation_docs() -> str:
    lines = ["## Deprecated APIs", ""]
    for meta in sorted(_REGISTRY.values(), key=lambda m: m.name):
        lines.append(f"### `{meta.name}`")
        lines.append(f"- **Replacement:** {meta.replacement}")
        lines.append(f"- **Removal target:** v{meta.removal_version}")
        lines.append(f"- **Subsystem:** {meta.subsystem}")
        lines.append(f"- **Since:** {meta.deprecated_since}")
        if meta.reason:
            lines.append(f"- **Reason:** {meta.reason}")
        lines.append("")
    return "\n".join(lines)
