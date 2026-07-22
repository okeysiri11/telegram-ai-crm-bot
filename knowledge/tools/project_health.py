#!/usr/bin/env python3
"""Generate PROJECT_HEALTH.md and refresh related dashboards."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from architecture_guardian import ArchitectureGuardian


def main() -> None:
    print(json.dumps(ArchitectureGuardian().project_health(), indent=2))


if __name__ == "__main__":
    main()
