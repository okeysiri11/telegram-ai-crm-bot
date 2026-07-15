"""analytics domain facade — empty strangler entrypoint.

Do not call from production handlers until migration phase.
"""

from __future__ import annotations


class AnalyticsFacade:
    """Scaffold facade for domain `analytics`."""

    domain = "analytics"

    def health(self) -> dict:
        return {"domain": self.domain, "scaffold": True}
