# Port ERP bridge — consume only, never modify Port ERP packages.

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PortERPBridge:
    """Native bridge to Port ERP without modifying applications/port_erp."""

    TARGET = "port_erp"

    def health(self) -> dict[str, Any]:
        try:
            from applications.port_erp import port_erp  # type: ignore

            h = port_erp.health() if hasattr(port_erp, "health") else {}
            return {"target": self.TARGET, "status": "reachable", "version": h.get("application_version", "unknown")}
        except Exception:
            logger.debug("port erp unavailable")
            return {"target": self.TARGET, "status": "unavailable", "mode": "stub"}

    def share_documents(self, document_id: str) -> dict[str, Any]:
        return {"shared": "documents", "document_id": document_id, "with": self.TARGET, "status": "queued"}

    def share_billing(self, invoice_id: str) -> dict[str, Any]:
        return {"shared": "billing", "invoice_id": invoice_id, "with": self.TARGET, "status": "queued"}


port_erp_bridge = PortERPBridge()
