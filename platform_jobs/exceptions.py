# Job Engine exceptions.

from __future__ import annotations


class JobError(Exception):
    """Base job engine error."""


class JobNotFoundError(JobError):
    """Job not registered or unknown id."""


class JobHandlerError(JobError):
    """Job handler missing or failed."""


class JobCancelledError(JobError):
    """Job was cancelled."""


class JobRetryExhaustedError(JobError):
    """Max retries exceeded — moved to dead letter."""


class SchedulerError(JobError):
    """Scheduler configuration error."""


class WorkerError(JobError):
    """Worker pool error."""
