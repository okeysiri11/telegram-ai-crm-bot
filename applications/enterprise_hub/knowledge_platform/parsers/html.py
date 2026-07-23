"""HtmlParser — document text extraction."""

from __future__ import annotations

from typing import Any


class HtmlParser:
    doc_type = "html"

    def parse(self, *, raw: str, title: str = "untitled") -> dict[str, Any]:
        text = raw if isinstance(raw, str) else str(raw)
        return {
            "doc_type": self.doc_type,
            "title": title,
            "content": text.strip(),
            "chars": len(text.strip()),
            "ocr": False,
        }
