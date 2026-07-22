#!/usr/bin/env python3
"""Full architecture review pipeline (Knowledge 1.3)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from architecture_guardian import ArchitectureGuardian


def main() -> None:
    result = ArchitectureGuardian().full_review()
    print(json.dumps(result, indent=2))
    print("\nSprint Knowledge 1.3 — full_architecture_review complete")


if __name__ == "__main__":
    main()
