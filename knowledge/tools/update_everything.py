#!/usr/bin/env python3
"""Run the full Documentation Assistant pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from documentation_assistant import DocumentationAssistant


def main() -> None:
    result = DocumentationAssistant().update_everything()
    print(json.dumps(result, indent=2, default=list))
    print("\nSprint Knowledge 1.2 — update_everything complete")


if __name__ == "__main__":
    main()
