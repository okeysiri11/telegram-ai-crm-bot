#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from enterprise_infra import EnterpriseInfrastructure

def main() -> None:
    eng = EnterpriseInfrastructure()
    eng.generate_pipeline()
    print(json.dumps({"status": "ok", "written": len(eng.written), "method": "generate_pipeline"}, indent=2))

if __name__ == "__main__":
    main()
