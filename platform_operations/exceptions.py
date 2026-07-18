# Operations dashboard exceptions.

from __future__ import annotations


class OperationsDashboardError(Exception):
    def __init__(self, message: str, *, status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


class WidgetNotFoundError(OperationsDashboardError):
    def __init__(self, widget_id: str) -> None:
        super().__init__(f"Unknown widget: {widget_id}", status=404)
