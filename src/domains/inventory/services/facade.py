"""inventory domain facade — empty strangler entrypoint.

Do not call from production handlers until migration phase.
"""

from __future__ import annotations


class InventoryFacade:
    """Scaffold facade for domain `inventory`."""

    domain = "inventory"

    def health(self) -> dict:
        return {"domain": self.domain, "scaffold": True}
