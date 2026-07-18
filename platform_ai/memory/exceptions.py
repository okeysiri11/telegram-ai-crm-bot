# AI Memory & Knowledge exceptions.

from __future__ import annotations


class MemoryError(Exception):
    """Base memory platform error."""


class MemoryNotFoundError(MemoryError):
    def __init__(self, memory_id: str) -> None:
        super().__init__(f"Memory not found: {memory_id}")
        self.memory_id = memory_id


class KnowledgeNotFoundError(MemoryError):
    def __init__(self, document_id: str) -> None:
        super().__init__(f"Knowledge document not found: {document_id}")
        self.document_id = document_id


class MemoryPermissionError(MemoryError):
    pass


class EmbeddingError(MemoryError):
    pass


class IndexError(MemoryError):
    pass
