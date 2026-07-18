# Document chunking strategies with metadata preservation.

from __future__ import annotations

import re
from typing import Any

from platform_ai.memory.models import ChunkStrategy, DocumentChunk


class Chunker:
    def chunk(
        self,
        text: str,
        document_id: str,
        *,
        strategy: str = ChunkStrategy.PARAGRAPH.value,
        chunk_size: int = 512,
        overlap: int = 64,
        metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        meta = dict(metadata or {})
        if strategy == ChunkStrategy.SENTENCE.value:
            parts = self._by_sentence(text)
        elif strategy == ChunkStrategy.PARAGRAPH.value:
            parts = self._by_paragraph(text)
        elif strategy == ChunkStrategy.SLIDING_WINDOW.value:
            parts = self._sliding_window(text, chunk_size, overlap)
        else:
            parts = self._fixed_size(text, chunk_size)

        chunks: list[DocumentChunk] = []
        for i, part in enumerate(parts):
            if not part.strip():
                continue
            chunk_meta = {**meta, "strategy": strategy, "chunk_index": i, "char_count": len(part)}
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{document_id}_chunk_{i}",
                    document_id=document_id,
                    content=part.strip(),
                    index=i,
                    metadata=chunk_meta,
                )
            )
        return chunks

    def _by_paragraph(self, text: str) -> list[str]:
        parts = re.split(r"\n\s*\n", text)
        return [p for p in parts if p.strip()]

    def _by_sentence(self, text: str) -> list[str]:
        parts = re.split(r"(?<=[.!?])\s+", text)
        return [p for p in parts if p.strip()]

    def _fixed_size(self, text: str, size: int) -> list[str]:
        return [text[i : i + size] for i in range(0, len(text), size)]

    def _sliding_window(self, text: str, size: int, overlap: int) -> list[str]:
        parts: list[str] = []
        step = max(size - overlap, 1)
        for i in range(0, len(text), step):
            part = text[i : i + size]
            if part.strip():
                parts.append(part)
        return parts


chunker = Chunker()
