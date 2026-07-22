#!/usr/bin/env python3
"""Incrementally update documentation from repository analysis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from documentation_assistant import DocumentationAssistant


def main() -> None:
    parser = argparse.ArgumentParser(description="Update docs incrementally")
    parser.add_argument("--force", action="store_true", help="Force broad refresh")
    args = parser.parse_args()
    result = DocumentationAssistant().update_docs(force=args.force)
    print(json.dumps(result, indent=2, default=list))


if __name__ == "__main__":
    main()
