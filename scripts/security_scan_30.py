#!/usr/bin/env python3
"""Lightweight security scan — Sprint 30.0 quality gate helper.

Checks for hardcoded insecure JWT defaults and direct os.environ in platform_security.
Exit 1 on findings.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAIL = 0

# platform_security must not read os.environ directly
for path in (ROOT / "platform_security").rglob("*.py"):
    text = path.read_text(encoding="utf-8", errors="ignore")
    if re.search(r"os\.environ", text):
        print(f"FAIL env_access {path.relative_to(ROOT)}")
        FAIL += 1

# jwt signing must go through jwt_secrets / configuration center
jwt_service = (ROOT / "platform_identity" / "jwt_service.py").read_text(encoding="utf-8")
if "resolve_iam_signing_secret" not in jwt_service:
    print("FAIL jwt_service missing resolve_iam_signing_secret")
    FAIL += 1

# Consent gate must exist
if not (ROOT / "platform_security" / "consent.py").exists():
    print("FAIL missing consent gate")
    FAIL += 1

if FAIL:
    print(f"security_scan failures={FAIL}")
    raise SystemExit(1)
print("security_scan OK")
raise SystemExit(0)
