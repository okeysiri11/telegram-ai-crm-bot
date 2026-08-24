#!/usr/bin/env python3
"""Copy Blender Odessa web export into src/web/public/assets/odessa (STEP 16)."""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE = Path.home() / "Desktop" / "ODESSA_WEB_EXPORT"
DEST = REPO / "src" / "web" / "public" / "assets" / "odessa"
PUBLIC_ROOT = "/assets/odessa"


def blender_bounds_to_city(b: dict) -> dict:
    """Blender manifest bounds (X, map-Y→Z, height-Z→Y) → Three.js CityBounds."""
    return {
        "minX": b["min_x"],
        "maxX": b["max_x"],
        "minZ": b["min_y"],
        "maxZ": b["max_y"],
        "minY": b.get("min_z", 0),
        "maxY": b.get("max_z", 0),
    }


def layer_for_type(asset_type: str) -> str:
    if asset_type.startswith("heavy_mesh"):
        return "heavy"
    return "city"


def main() -> int:
    src_manifest_path = SOURCE / "odessa_manifest.json"
    if not src_manifest_path.exists():
        raise SystemExit(f"Source manifest missing: {src_manifest_path}")

    raw = json.loads(src_manifest_path.read_text())
    assets = raw["assets"]

    missing: list[str] = []
    copied = 0
    total_bytes = 0
    largest = ("", 0)

    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True, exist_ok=True)

    runtime_assets = []
    bounds_list = []

    for a in assets:
        rel = a["path"]
        src = SOURCE / rel
        if not src.exists() or src.stat().st_size <= 0:
            missing.append(rel)
            continue
        dst = DEST / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
        sz = src.stat().st_size
        total_bytes += sz
        if sz > largest[1]:
            largest = (rel, sz)

        url = f"{PUBLIC_ROOT}/{rel.replace(chr(92), '/')}"
        city_bounds = None
        if "bounds" in a:
            city_bounds = blender_bounds_to_city(a["bounds"])
            bounds_list.append(city_bounds)

        runtime_assets.append(
            {
                **a,
                "url": url,
                "layer": layer_for_type(a.get("type", "")),
            }
        )

    if missing:
        raise SystemExit(f"Missing GLBs after copy: {missing}")

    # Combined bounds + priority (closest to city center in scene XZ)
    combined = None
    if bounds_list:
        combined = {
            "minX": min(b["minX"] for b in bounds_list),
            "maxX": max(b["maxX"] for b in bounds_list),
            "minZ": min(b["minZ"] for b in bounds_list),
            "maxZ": max(b["maxZ"] for b in bounds_list),
            "minY": min(b.get("minY", 0) for b in bounds_list),
            "maxY": max(b.get("maxY", 0) for b in bounds_list),
        }
        cx = (combined["minX"] + combined["maxX"]) / 2
        cz = (combined["minZ"] + combined["maxZ"]) / 2

        def dist(a: dict) -> float:
            b = blender_bounds_to_city(a["bounds"]) if "bounds" in a else None
            if not b:
                return 1e9
            ax = (b["minX"] + b["maxX"]) / 2
            az = (b["minZ"] + b["maxZ"]) / 2
            return math.hypot(ax - cx, az - cz)

        priority = [a["id"] for a in sorted([x for x in assets if "bounds" in x], key=dist)[:8]]
    else:
        priority = [assets[0]["id"]] if assets else []

    runtime = {
        "name": raw.get("name", "Odessa 3D Web Map"),
        "version": raw.get("version", 1),
        "packageFormat": "blender_web_v1",
        "coordinate_system": raw.get("coordinate_system"),
        "loading_strategy": raw.get("loading_strategy"),
        "notes": raw.get("notes", []),
        "stats": raw.get("stats", {}),
        "geoTransform": {
            "originLat": 46.4825,
            "originLng": 30.7233,
            "calibrated": False,
        },
        "cityBounds": combined,
        "priorityAssets": priority,
        "layers": [
            {"id": "city", "label": "Odessa city", "defaultVisible": True},
            {"id": "heavy", "label": "Heavy buildings", "defaultVisible": True},
            {"id": "dynamic", "label": "Live data", "defaultVisible": True, "dynamic": True},
        ],
        "assets": runtime_assets,
    }

    out_path = DEST / "odessa_manifest.json"
    out_path.write_text(json.dumps(runtime, indent=2), encoding="utf-8")

    print("SOURCE EXPORT: FOUND")
    print(f"MANIFEST ASSETS: {len(assets)}")
    print(f"COPIED REAL GLBs: {copied}")
    print(f"MISSING: {len(missing)}")
    print(f"TOTAL SIZE MB: {total_bytes / 1024 / 1024:.3f}")
    print(f"LARGEST FILE: {largest[0]} ({largest[1] / 1024 / 1024:.3f} MB)")
    print(f"RUNTIME MANIFEST: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
