#!/usr/bin/env python3
"""Regenerate Mermaid architecture / dependency / agent graphs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from documentation_assistant import DocumentationAssistant


def main() -> None:
    parser = argparse.ArgumentParser(description="Build automated Mermaid graphs")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    result = DocumentationAssistant().build_graph(force=args.force)
    print(json.dumps(result, indent=2, default=list))


if __name__ == "__main__":
    main()
