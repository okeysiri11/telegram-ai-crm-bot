# Response parser — normalize provider responses.

from __future__ import annotations

import json
import re
from typing import Any

from platform_ai.provider_base import ProviderResponse


class ResponseParser:
    JSON_BLOCK = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```")

    def parse_text(self, response: ProviderResponse) -> str:
        return response.content.strip()

    def parse_json(self, response: ProviderResponse) -> dict[str, Any]:
        content = response.content.strip()
        match = self.JSON_BLOCK.search(content)
        if match:
            content = match.group(1)
        try:
            result = json.loads(content)
            return result if isinstance(result, dict) else {"value": result}
        except json.JSONDecodeError:
            return {"raw": content}

    def parse_classification(self, response: ProviderResponse, labels: list[str]) -> dict[str, Any]:
        text = self.parse_text(response).lower()
        for label in labels:
            if label.lower() in text:
                return {"label": label, "confidence": 0.8, "raw": response.content}
        return {"label": labels[0] if labels else "unknown", "confidence": 0.5, "raw": response.content}


response_parser = ResponseParser()
