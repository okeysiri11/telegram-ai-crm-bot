"""Shared exceptions — Enterprise Hub."""


class HubError(Exception):
    """Base hub error."""


class ValidationError(HubError):
    """Invalid input."""


class NotFoundError(HubError):
    """Missing entity."""
