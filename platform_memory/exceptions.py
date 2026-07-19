# Platform Memory — domain exceptions.

from __future__ import annotations


class MemoryError(Exception):
    """Base memory subsystem error."""


class MemoryNotFoundError(MemoryError):
    def __init__(self, identifier: str) -> None:
        super().__init__(f"Memory not found: {identifier}")
        self.identifier = identifier


class MemoryValidationError(MemoryError):
    pass


class ContextAssemblyError(MemoryError):
    pass
