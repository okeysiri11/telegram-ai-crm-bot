"""Shared exceptions — Platform Builder."""

from __future__ import annotations


class PlatformBuilderError(Exception):
    pass


class ValidationError(PlatformBuilderError):
    pass


class NotFoundError(PlatformBuilderError):
    pass


class ForbiddenError(PlatformBuilderError):
    pass
