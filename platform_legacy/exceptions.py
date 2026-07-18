# Legacy adapter exceptions.

from __future__ import annotations


class LegacyAdapterError(Exception):
    """Base error for legacy adapter failures."""


class LegacyUnavailableError(LegacyAdapterError):
    """Legacy subsystem is not available or not wired."""


class LegacyImportViolationError(LegacyAdapterError):
    """Platform code attempted a forbidden legacy import."""
