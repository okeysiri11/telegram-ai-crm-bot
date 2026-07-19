# Platform manifest — single source of truth for agents, CI, and verticals.

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

MANIFEST_VERSION = "1.0.0"
CORE_VERSION = "1.0.0-rc1"
ARCHITECTURE_VERSION = "1.0.0"


def _file_sha256(path: Path) -> str:
    if not path.is_file():
        return ""
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def build_manifest(
    *,
    certification: dict[str, Any],
    metrics: dict[str, object],
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    modules = sorted(
        p.name
        for p in ROOT.iterdir()
        if p.is_dir() and (p.name.startswith("platform_") or p.name in {"events", "repositories", "plugins"})
    )
    return {
        "manifest_version": MANIFEST_VERSION,
        "generated_at": now,
        "platform_core": {
            "version": CORE_VERSION,
            "architecture_version": ARCHITECTURE_VERSION,
            "api_contract_version": "1.0.0",
            "api_version": "v1",
            "certification_status": certification.get("verdict", "FAIL"),
            "certification_score": certification.get("overall_score", 0),
        },
        "modules": modules,
        "sdk": {
            "plugin_sdk_version": "1.0.0",
            "platform_sdk_path": "platform_sdk/",
        },
        "apis": {
            "management": "/management/v1",
            "public": "/api/v1",
            "legacy_public": "/v1",
            "legacy_management": "/management",
        },
        "certification": {
            "sprint": "1.5",
            "verdict": certification.get("verdict"),
            "release_readiness": certification.get("release_readiness"),
            "gates_passed": certification.get("gates_passed"),
            "gates_total": certification.get("gates_total"),
            "checks": checks,
        },
        "metrics": metrics,
        "integrity_hashes": {
            "platform_api_contracts": _file_sha256(ROOT / "platform_api" / "contracts.py"),
            "platform_plugin_sdk_init": _file_sha256(ROOT / "platform_plugin_sdk" / "__init__.py"),
            "platform_architecture_governance": _file_sha256(ROOT / "platform_architecture" / "governance.py"),
            "platform_manifest_self": "",
        },
        "agents": {
            "description": "Authoritative platform metadata for AI agents, CI/CD, and vertical modules",
            "supported_verticals": ["auto", "agro", "realty", "legal", "logistics", "medical", "insurance", "construction"],
            "rules": [
                "Use platform_legacy for legacy access",
                "Use platform_plugin_sdk for plugins",
                "Use /management/v1 for admin operations",
                "Never import services.pg_* from platform modules",
            ],
        },
    }


def write_manifest(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(data)
    payload["integrity_hashes"]["platform_manifest_self"] = ""
    text = json.dumps(payload, indent=2, sort_keys=False)
    payload["integrity_hashes"]["platform_manifest_self"] = hashlib.sha256(text.encode()).hexdigest()
    final_text = json.dumps(payload, indent=2, sort_keys=False) + "\n"
    path.write_text(final_text, encoding="utf-8")
    yaml_path = path.with_suffix(".yaml")
    try:
        import yaml  # type: ignore

        yaml_path.write_text(yaml.dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    except Exception:
        pass
    return path
