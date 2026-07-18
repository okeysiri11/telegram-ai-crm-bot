# Knowledge loader — ingest Markdown, PDF, DOCX, TXT, HTML, JSON, YAML, CSV.

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any

from platform_ai.memory.models import KnowledgeType


class KnowledgeLoader:
    def load(self, content: str | bytes, doc_type: str, *, title: str = "") -> dict[str, Any]:
        if doc_type == KnowledgeType.JSON.value:
            return self._load_json(content)
        if doc_type == KnowledgeType.YAML.value:
            return self._load_yaml(content)
        if doc_type == KnowledgeType.CSV.value:
            return self._load_csv(content)
        if doc_type == KnowledgeType.HTML.value:
            return self._load_html(content)
        if doc_type == KnowledgeType.MARKDOWN.value:
            return self._load_markdown(content)
        if doc_type in (KnowledgeType.PDF.value, KnowledgeType.DOCX.value):
            return self._load_binary_placeholder(content, doc_type, title)
        return self._load_text(content)

    def _load_text(self, content: str | bytes) -> dict[str, Any]:
        text = content.decode() if isinstance(content, bytes) else content
        return {"text": text, "metadata": {"format": "text"}}

    def _load_markdown(self, content: str | bytes) -> dict[str, Any]:
        text = content.decode() if isinstance(content, bytes) else content
        headers = re.findall(r"^#+\s+(.+)$", text, re.MULTILINE)
        return {"text": text, "metadata": {"format": "markdown", "headers": headers}}

    def _load_html(self, content: str | bytes) -> dict[str, Any]:
        text = content.decode() if isinstance(content, bytes) else content
        stripped = re.sub(r"<[^>]+>", " ", text)
        stripped = re.sub(r"\s+", " ", stripped).strip()
        return {"text": stripped, "metadata": {"format": "html", "raw_length": len(text)}}

    def _load_json(self, content: str | bytes) -> dict[str, Any]:
        text = content.decode() if isinstance(content, bytes) else content
        data = json.loads(text)
        return {"text": json.dumps(data, indent=2, ensure_ascii=False), "metadata": {"format": "json"}}

    def _load_yaml(self, content: str | bytes) -> dict[str, Any]:
        text = content.decode() if isinstance(content, bytes) else content
        try:
            import yaml

            data = yaml.safe_load(text)
            return {"text": yaml.dump(data, default_flow_style=False), "metadata": {"format": "yaml"}}
        except ImportError:
            return {"text": text, "metadata": {"format": "yaml", "parsed": False}}

    def _load_csv(self, content: str | bytes) -> dict[str, Any]:
        text = content.decode() if isinstance(content, bytes) else content
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        lines = [" | ".join(row) for row in rows]
        return {"text": "\n".join(lines), "metadata": {"format": "csv", "rows": len(rows)}}

    def _load_binary_placeholder(self, content: str | bytes, doc_type: str, title: str) -> dict[str, Any]:
        size = len(content) if isinstance(content, bytes) else len(content.encode())
        return {
            "text": f"[{doc_type.upper()} document: {title or 'untitled'}, {size} bytes]",
            "metadata": {"format": doc_type, "binary": True, "size": size},
        }


knowledge_loader = KnowledgeLoader()
