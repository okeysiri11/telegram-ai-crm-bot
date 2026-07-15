"""logistics domain facade — empty strangler entrypoint.

Do not call from production handlers until migration phase.
"""

from __future__ import annotations


class LogisticsFacade:
    """Scaffold facade for domain `logistics`."""

    domain = "logistics"

    def health(self) -> dict:
        return {"domain": self.domain, "scaffold": True}
