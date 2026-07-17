"""Layered architecture primitives — repositories, services, session policy."""

from src.platform.layers.base_repository import BaseRepository
from src.platform.layers.base_service import BaseService
from src.platform.layers.session_policy import (
    HANDLER_SESSION_FORBIDDEN,
    SESSION_ALLOWED_MODULES,
    assert_handler_session_policy,
)

__all__ = [
    "BaseRepository",
    "BaseService",
    "HANDLER_SESSION_FORBIDDEN",
    "SESSION_ALLOWED_MODULES",
    "assert_handler_session_policy",
]
