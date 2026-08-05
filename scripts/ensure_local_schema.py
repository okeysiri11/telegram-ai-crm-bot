#!/usr/bin/env python3
"""Sprint 32.6B — apply Alembic migrations for local zero-touch launch.

Usage:
  ./venv/bin/python scripts/ensure_local_schema.py
  ADOS_SKIP_MIGRATIONS=1 …  # no-op
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger("ensure_local_schema")


def ensure_schema(*, timeout_sec: int = 300) -> int:
    """Run `alembic upgrade head`. Returns 0 on success, non-zero on failure."""
    if os.getenv("ADOS_SKIP_MIGRATIONS", "").lower() in {"1", "true", "yes"}:
        logger.info("ADOS_SKIP_MIGRATIONS set — skipping alembic")
        return 0

    py = sys.executable
    cmd = [py, "-m", "alembic", "upgrade", "head"]
    logger.info("running: %s (cwd=%s)", " ".join(cmd), ROOT)
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(ROOT),
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
    except subprocess.TimeoutExpired:
        logger.error("alembic upgrade head timed out after %ss", timeout_sec)
        return 1
    except FileNotFoundError:
        logger.error("python/alembic not available via %s", py)
        return 1

    if completed.stdout:
        for line in completed.stdout.strip().splitlines()[-40:]:
            logger.info("alembic: %s", line)
    if completed.returncode != 0:
        err = (completed.stderr or completed.stdout or "").strip()
        for line in err.splitlines()[-60:]:
            logger.error("alembic: %s", line)
        return completed.returncode or 1

    logger.info("schema migrations applied (alembic upgrade head)")
    return 0


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except Exception:
        pass
    raise SystemExit(ensure_schema())


if __name__ == "__main__":
    main()
