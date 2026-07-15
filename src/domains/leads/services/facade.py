"""leads domain facade — empty strangler entrypoint.

Do not call from production handlers until migration phase.
"""

from __future__ import annotations


class LeadsFacade:
    """Scaffold facade for domain `leads`."""

    domain = "leads"

    def health(self) -> dict:
        return {"domain": self.domain, "scaffold": True}
