"""automotive domain facade — empty strangler entrypoint.

Do not call from production handlers until migration phase.
"""

from __future__ import annotations


class AutomotiveFacade:
    """Scaffold facade for domain `automotive`."""

    domain = "automotive"

    def health(self) -> dict:
        return {"domain": self.domain, "scaffold": True}
