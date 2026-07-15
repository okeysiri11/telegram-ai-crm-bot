"""legal domain facade — empty strangler entrypoint.

Do not call from production handlers until migration phase.
"""

from __future__ import annotations


class LegalFacade:
    """Scaffold facade for domain `legal`."""

    domain = "legal"

    def health(self) -> dict:
        return {"domain": self.domain, "scaffold": True}
