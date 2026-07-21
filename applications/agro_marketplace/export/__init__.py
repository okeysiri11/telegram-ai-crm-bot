"""Export package — international trade and shipment workflow."""

from __future__ import annotations

from typing import Any

__all__ = ["ExportEngine", "ExportService", "export_engine", "export_service"]


def __getattr__(name: str) -> Any:
    if name in {"ExportEngine", "export_engine"}:
        from applications.agro_marketplace.export.engine import ExportEngine, export_engine

        return ExportEngine if name == "ExportEngine" else export_engine
    if name in {"ExportService", "export_service"}:
        from applications.agro_marketplace.export.service import ExportService, export_service

        return ExportService if name == "ExportService" else export_service
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
