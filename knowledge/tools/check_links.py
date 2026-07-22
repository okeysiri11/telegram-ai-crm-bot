#!/usr/bin/env python3
"""Validate wiki links and documentation completeness."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from documentation_assistant import DocumentationAssistant


def main() -> None:
    result = DocumentationAssistant().check_links()
    print(json.dumps(result, indent=2, default=list))
    print("Wrote knowledge/VALIDATION_REPORT.md")


if __name__ == "__main__":
    main()
