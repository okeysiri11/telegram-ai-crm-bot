#!/usr/bin/env python3
"""Refresh INDEX and project dashboards."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from documentation_assistant import DocumentationAssistant


def main() -> None:
    result = DocumentationAssistant().update_dashboards_only(force=True)
    print(json.dumps(result, indent=2, default=list))


if __name__ == "__main__":
    main()
