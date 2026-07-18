# Observability platform exceptions.

from __future__ import annotations


class ObservabilityError(Exception):
    """Base observability error."""


class MetricError(ObservabilityError):
    """Metric recording or export failure."""


class TraceError(ObservabilityError):
    """Tracing failure."""


class AlertError(ObservabilityError):
    """Alert management failure."""


class RetentionError(ObservabilityError):
    """Retention policy failure."""
