"""payments domain facade — empty strangler entrypoint.

Do not call from production handlers until migration phase.
"""

from __future__ import annotations


class PaymentsFacade:
    """Scaffold facade for domain `payments`."""

    domain = "payments"

    def health(self) -> dict:
        return {"domain": self.domain, "scaffold": True}
