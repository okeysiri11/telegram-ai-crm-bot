#!/usr/bin/env python3
"""Security marker audit — Sprint 30.0.

Searches backend Python for TODO/FIXME/HACK/temporary/deprecated/legacy/unsafe/
password/secret/jwt/token/admin/superuser markers and writes a documented report.
Does not modify production behavior — documentation + triage.
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    "TODO",
    "FIXME",
    "HACK",
    "temporary",
    "deprecated",
    "legacy",
    "unsafe",
    "password",
    "secret",
    "jwt",
    "token",
    "admin",
    "superuser",
]
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "__pycache__",
    ".mypy_cache",
    "src/web",
    "platform_console",
    "docs",
}


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIRS:
        return True
    for skip in SKIP_DIRS:
        if skip in str(path):
            return True
    return False


def main() -> int:
    counts: Counter[str] = Counter()
    samples: dict[str, list[str]] = defaultdict(list)
    rx = re.compile("|".join(re.escape(p) for p in PATTERNS), re.I)

    for path in ROOT.rglob("*.py"):
        if should_skip(path.relative_to(ROOT)):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if not rx.search(line):
                continue
            for pat in PATTERNS:
                if re.search(pat, line, re.I):
                    counts[pat] += 1
                    if len(samples[pat]) < 8:
                        rel = path.relative_to(ROOT)
                        samples[pat].append(f"`{rel}:{i}` — `{line.strip()[:120]}`")

    out = ROOT / "docs" / "SECURITY_MARKER_AUDIT.md"
    lines = [
        "# Security Marker Audit — Sprint 30.0",
        "",
        "Automated scan of backend `*.py` for security-relevant markers.",
        "Occurrences are **documented**, not auto-deleted (many are legitimate).",
        "",
        "## Counts",
        "",
        "| Marker | Count |",
        "|---|---:|",
    ]
    for pat in PATTERNS:
        lines.append(f"| `{pat}` | {counts[pat]} |")
    lines.extend(["", "## Samples (up to 8 per marker)", ""])
    for pat in PATTERNS:
        lines.append(f"### `{pat}`")
        lines.append("")
        if not samples[pat]:
            lines.append("_none_")
        else:
            for s in samples[pat]:
                lines.append(f"- {s}")
        lines.append("")
    lines.extend(
        [
            "## Disposition policy",
            "",
            "- **Remove** only confirmed dead/unsafe code in a dedicated PR.",
            "- **Document** intentional legacy/deprecated markers in `TECH_DEBT.md`.",
            "- **Never** commit real passwords/secrets — if found, rotate immediately.",
            "",
            "Hardening applied this sprint lives in `platform_security/`, `middleware/security_middleware.py`,",
            "`repositories/tenant_scope.py`, and Platform Builder live-auth middleware.",
            "",
        ]
    )
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} total_hits={sum(counts.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
