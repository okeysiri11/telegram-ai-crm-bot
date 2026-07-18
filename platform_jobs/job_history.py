# Job execution history.

from __future__ import annotations

from platform_jobs.models import JobRecord


class JobHistory:
    def __init__(self, *, max_entries: int = 10_000) -> None:
        self._entries: list[JobRecord] = []
        self._max_entries = max_entries

    def reset(self) -> None:
        self._entries.clear()

    def record(self, job: JobRecord) -> None:
        self._entries.append(job)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries :]

    def list(self, *, limit: int = 100) -> list[dict]:
        return [j.to_dict() for j in self._entries[-limit:]]

    def by_handler(self, handler_name: str, *, limit: int = 50) -> list[dict]:
        matched = [j for j in self._entries if j.handler_name == handler_name]
        return [j.to_dict() for j in matched[-limit:]]


job_history = JobHistory()
