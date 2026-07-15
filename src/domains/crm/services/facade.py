"""crm domain facade — empty strangler entrypoint.

Do not call from production handlers until migration phase.
"""

from __future__ import annotations


class CrmFacade:
    """Scaffold facade for domain `crm`."""

    domain = "crm"

    def health(self) -> dict:
        return {"domain": self.domain, "scaffold": True}
