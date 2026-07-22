#!/usr/bin/env python3
"""Run full Knowledge 2.0 enterprise infrastructure generation + core doc refresh."""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from enterprise_infra import EnterpriseInfrastructure

def main() -> None:
    result = EnterpriseInfrastructure().run_all()
    print(json.dumps(result, indent=2))
    print("\nSprint Knowledge 2.0 — enterprise update complete")

if __name__ == "__main__":
    main()
