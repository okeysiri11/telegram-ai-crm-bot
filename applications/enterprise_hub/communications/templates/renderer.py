"""Template renderer — Markdown / HTML / Plain with {{variables}}."""

from __future__ import annotations

import re
from typing import Any

from applications.enterprise_hub.communications.models import TEMPLATE_FORMATS
from applications.enterprise_hub.shared.exceptions import ValidationError

_VAR = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def render_template(template: str, variables: dict[str, Any] | None = None, fmt: str = "plain") -> str:
    fmt_n = (fmt or "plain").lower().strip()
    if fmt_n not in TEMPLATE_FORMATS:
        raise ValidationError(f"format must be one of {list(TEMPLATE_FORMATS)}")
    vars_map = variables or {}

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return str(vars_map.get(key, match.group(0)))

    text = _VAR.sub(repl, template or "")
    if fmt_n == "html":
        return f"<div>{text}</div>"
    if fmt_n == "markdown":
        return text
    return text
