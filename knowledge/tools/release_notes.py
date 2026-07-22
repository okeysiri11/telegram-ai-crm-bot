#!/usr/bin/env python3
"""Generate RELEASE_NOTES.md and CHANGELOG.md from Git + scans."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from documentation_assistant import DocumentationAssistant


def main() -> None:
    result = DocumentationAssistant().release_notes_only()
    print(json.dumps(result, indent=2, default=list))


if __name__ == "__main__":
    main()
