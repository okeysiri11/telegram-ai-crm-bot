#!/usr/bin/env python3
"""Bootstrap a new business plugin from the official SDK template."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent / "template"
PLUGINS_ROOT = Path(__file__).resolve().parents[1] / "plugins"

SUBDIRS = (
    "workflow",
    "handlers",
    "services",
    "routes",
    "messages",
    "permissions",
    "config",
    "migrations",
    "assets",
)


def _class_name(plugin_id: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[_-]", plugin_id)) + "Plugin"


def bootstrap(
    plugin_id: str,
    name: str,
    *,
    author: str = "Developer",
    description: str = "",
    vertical_code: str | None = None,
    root: Path | None = None,
) -> Path:
    if not re.match(r"^[a-z][a-z0-9_-]*$", plugin_id):
        raise ValueError("plugin_id must be lowercase slug (e.g. finance)")

    target = (root or PLUGINS_ROOT) / plugin_id
    if target.exists():
        raise FileExistsError(f"Plugin directory already exists: {target}")

    target.mkdir(parents=True)
    for sub in SUBDIRS:
        (target / sub).mkdir()
        (target / sub / ".gitkeep").touch()

    replacements = {
        "{{PLUGIN_ID}}": plugin_id,
        "{{PLUGIN_NAME}}": name,
        "{{PLUGIN_CLASS}}": _class_name(plugin_id),
        "{{AUTHOR}}": author,
        "{{DESCRIPTION}}": description or f"{name} business domain plugin",
        "{{VERTICAL_CODE}}": (vertical_code or plugin_id).upper(),
    }

    for tpl_name, out_name in (("plugin.py.tpl", "plugin.py"), ("manifest.yaml.tpl", "manifest.yaml")):
        tpl = (TEMPLATE_DIR / tpl_name).read_text(encoding="utf-8")
        for key, value in replacements.items():
            tpl = tpl.replace(key, value)
        (target / out_name).write_text(tpl, encoding="utf-8")

    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap a Platform Plugin from SDK template")
    parser.add_argument("plugin_id", help="Plugin id (e.g. finance)")
    parser.add_argument("--name", required=True, help="Display name")
    parser.add_argument("--author", default="Developer")
    parser.add_argument("--description", default="")
    parser.add_argument("--vertical", default=None, help="Vertical code override")
    parser.add_argument("--root", type=Path, default=None, help="Plugins root directory")
    args = parser.parse_args(argv)

    path = bootstrap(
        args.plugin_id,
        args.name,
        author=args.author,
        description=args.description,
        vertical_code=args.vertical,
        root=args.root,
    )
    print(f"Created plugin at {path}")
    print("Next steps:")
    print(f"  1. Implement handlers in {path}/handlers/")
    print(f"  2. POST /management/plugins/{args.plugin_id}/install")
    print(f"  3. POST /management/plugins/{args.plugin_id}/enable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
