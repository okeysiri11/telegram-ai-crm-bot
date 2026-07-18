# AI Platform exceptions.

from __future__ import annotations


class AIPlatformError(Exception):
    """Base AI platform error."""


class AIProviderNotFoundError(AIPlatformError):
    pass


class AIProviderUnavailableError(AIPlatformError):
    pass


class AIModelNotFoundError(AIPlatformError):
    pass


class AIPromptValidationError(AIPlatformError):
    pass


class AICacheError(AIPlatformError):
    pass


class AIRoutingError(AIPlatformError):
    pass


class AICostThresholdError(AIPlatformError):
    pass
