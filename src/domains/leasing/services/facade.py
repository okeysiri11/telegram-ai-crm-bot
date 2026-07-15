"""leasing domain facade — empty strangler entrypoint.

Do not call from production handlers until migration phase.
"""

from __future__ import annotations


class LeasingFacade:
    """Scaffold facade for domain `leasing`."""

    domain = "leasing"

    def health(self) -> dict:
        return {"domain": self.domain, "scaffold": True}
