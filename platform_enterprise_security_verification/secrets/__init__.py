"""Secret Scanner — Sprint 25.5."""

from __future__ import annotations

from typing import Any

from platform_enterprise_security_verification.models import SECRET_PATTERNS


class SecretScanner:
    def scan(self, *, hits: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        hits = list(hits or [])
        # reject raw secrets in report values
        for h in hits:
            val = str(h.get("value", ""))
            if val.startswith("sk-") or "BEGIN PRIVATE KEY" in val:
                raise ValueError("secret scanner must report references only, never raw secrets")
        by_type = {p: [h for h in hits if h.get("type") == p] for p in SECRET_PATTERNS}
        return {
            "domain": "secrets",
            "patterns": list(SECRET_PATTERNS),
            "hits": hits,
            "by_type": {k: len(v) for k, v in by_type.items()},
            "passed": len(hits) == 0,
            "raw_secrets_exposed": False,
        }
