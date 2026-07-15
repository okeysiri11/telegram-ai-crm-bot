"""insurance domain facade — empty strangler entrypoint.

Do not call from production handlers until migration phase.
"""

from __future__ import annotations


class InsuranceFacade:
    """Scaffold facade for domain `insurance`."""

    domain = "insurance"

    def health(self) -> dict:
        return {"domain": self.domain, "scaffold": True}
