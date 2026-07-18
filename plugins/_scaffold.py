#!/usr/bin/env python3
"""Scaffold plugin manifest and entry module for a business domain."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent

PLUGINS = [
    {
        "id": "auto",
        "name": "Automotive",
        "description": "Automotive dealership and vehicle sales vertical",
        "permissions": ["auto.read", "auto.write", "requests.read"],
        "workflows": ["auto_buy", "auto_sell"],
        "config": {"vertical_code": "AUTO", "manager_strategy": "SMART"},
    },
    {
        "id": "realty",
        "name": "Real Estate",
        "description": "Real estate listings and property management vertical",
        "permissions": ["realty.read", "realty.write", "requests.read"],
        "workflows": ["realty_post_create", "realty_listing"],
        "config": {"vertical_code": "REALTY", "manager_strategy": "SMART"},
    },
    {
        "id": "agro",
        "name": "Agro",
        "description": "Agricultural products and farm services vertical",
        "permissions": ["agro.read", "agro.write", "requests.read"],
        "workflows": ["agro_request"],
        "config": {"vertical_code": "AGRO", "manager_strategy": "SMART"},
    },
    {
        "id": "legal",
        "name": "Legal Services",
        "description": "Legal consultation and document services vertical",
        "permissions": ["legal.read", "legal.write", "requests.read"],
        "workflows": ["legal_consultation"],
        "config": {"vertical_code": "LEGAL", "manager_strategy": "SMART"},
    },
    {
        "id": "insurance",
        "name": "Insurance",
        "description": "Insurance products and policy management vertical",
        "permissions": ["insurance.read", "insurance.write"],
        "workflows": ["insurance_quote"],
        "config": {"vertical_code": "INSURANCE"},
        "optional_deps": [{"id": "auto", "version": ">=1.0.0"}],
    },
    {
        "id": "construction",
        "name": "Construction",
        "description": "Construction projects and contractor services vertical",
        "permissions": ["construction.read", "construction.write"],
        "workflows": ["construction_project"],
        "config": {"vertical_code": "CONSTRUCTION"},
        "required_deps": [{"id": "legal", "version": ">=1.0.0"}],
    },
    {
        "id": "medical",
        "name": "Medical",
        "description": "Medical appointments and healthcare services vertical",
        "permissions": ["medical.read", "medical.write"],
        "workflows": ["medical_appointment"],
        "config": {"vertical_code": "MEDICAL"},
    },
]

MANIFEST_TEMPLATE = """id: {id}
name: {name}
version: 1.0.0
author: Platform Team
description: {description}
platform_version: ">=1.0.0"
dependencies:
  required: {required}
  optional: {optional}
permissions: {permissions_yaml}
configuration: {config_yaml}
routes:
  - path: /{id}
    handler: routes.{id}_router:register
workflows: {workflows_yaml}
entry_point: plugin:register
"""

PLUGIN_PY = '''"""Plugin entry point — {name}."""


def register(ctx):
    ctx.log("{name} plugin registered")
    return {{"plugin_id": ctx.plugin_id, "status": "registered"}}


async def on_enable(ctx):
    ctx.log("{name} plugin enabled")


async def on_disable(ctx):
    ctx.log("{name} plugin disabled")


async def health(ctx):
    return {{"status": "healthy", "domain": "{id}"}}
'''


def yaml_list(items):
    if not items:
        return "[]"
    lines = "\n".join(f'  - "{x}"' if isinstance(x, str) else f"  - {x}" for x in items)
    return f"\n{lines}"


def yaml_deps(deps):
    if not deps:
        return "[]"
    lines = []
    for d in deps:
        lines.append(f"    - id: {d['id']}\n      version: \"{d['version']}\"")
    return "\n" + "\n".join(lines)


def yaml_config(cfg):
    lines = "\n".join(f"  {k}: {v if not isinstance(v, str) else repr(v)}" for k, v in cfg.items())
    return f"\n{lines}"


def main():
    for spec in PLUGINS:
        plugin_dir = ROOT / spec["id"]
        plugin_dir.mkdir(parents=True, exist_ok=True)
        manifest = MANIFEST_TEMPLATE.format(
            id=spec["id"],
            name=spec["name"],
            description=spec["description"],
            required=yaml_deps(spec.get("required_deps", [])),
            optional=yaml_deps(spec.get("optional_deps", [])),
            permissions_yaml=yaml_list(spec["permissions"]),
            config_yaml=yaml_config(spec["config"]),
            workflows_yaml=yaml_list(spec["workflows"]),
        )
        (plugin_dir / "manifest.yaml").write_text(manifest, encoding="utf-8")
        (plugin_dir / "plugin.py").write_text(
            PLUGIN_PY.format(id=spec["id"], name=spec["name"]),
            encoding="utf-8",
        )
        for sub in (
            "workflow",
            "handlers",
            "services",
            "routes",
            "messages",
            "permissions",
            "config",
            "migrations",
            "assets",
        ):
            (plugin_dir / sub).mkdir(exist_ok=True)
            gitkeep = plugin_dir / sub / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
        print(f"scaffolded {spec['id']}")


if __name__ == "__main__":
    main()
