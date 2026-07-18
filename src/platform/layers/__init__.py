"""Layered architecture primitives — repositories, services, session policy."""

from src.platform.layers.base_repository import BaseRepository
from src.platform.layers.base_service import BaseService
from src.platform.layers.session_policy import (
    HANDLER_SESSION_FORBIDDEN,
    SESSION_ALLOWED_MODULES,
    assert_handler_session_policy,
    scan_handler_session_violations,
)
from src.platform.layers.architecture_policy import (
    BoundaryViolation,
    scan_architecture_violations,
    scan_layer,
    scan_file,
)

__all__ = [
    "BaseRepository",
    "BaseService",
    "BoundaryViolation",
    "HANDLER_SESSION_FORBIDDEN",
    "SESSION_ALLOWED_MODULES",
    "assert_handler_session_policy",
    "scan_handler_session_violations",
    "scan_architecture_violations",
    "scan_layer",
    "scan_file",
]
