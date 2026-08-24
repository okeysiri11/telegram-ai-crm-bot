#!/usr/bin/env python3
"""Verify Odessa runtime manifest URLs map to real GLB files with valid headers."""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUBLIC = REPO / "src" / "web" / "public"
MANIFEST = PUBLIC / "assets" / "odessa" / "odessa_manifest.json"


def glb_magic_ok(path: Path) -> bool:
    with path.open("rb") as f:
        head = f.read(4)
    return head == b"glTF"


def main() -> int:
    if not MANIFEST.exists():
        print(f"FAIL manifest missing: {MANIFEST}")
        return 1

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assets = data.get("assets") or []
    ids: set[str] = set()
    urls: set[str] = set()
    missing = 0
    bad_magic = 0
    total_bytes = 0
    largest = ("", 0)

    print(f"{'ID':<40} {'EXISTS':<6} {'SIZE_MB':<10} {'MAGIC':<6} URL")
    print("-" * 120)

    for a in assets:
        aid = a["id"]
        url = a.get("url") or ""
        dup_id = aid in ids
        dup_url = url in urls
        ids.add(aid)
        urls.add(url)

        rel = url.replace("/assets/odessa/", "").lstrip("/")
        if url.startswith("/assets/odessa/"):
            fp = PUBLIC / "assets" / "odessa" / rel
        else:
            fp = PUBLIC / rel.lstrip("/")

        exists = fp.exists() and fp.stat().st_size > 0
        sz = fp.stat().st_size if exists else 0
        magic = glb_magic_ok(fp) if exists and fp.suffix.lower() == ".glb" else False
        if exists:
            total_bytes += sz
            if sz > largest[1]:
                largest = (str(fp.relative_to(PUBLIC)), sz)
        else:
            missing += 1
        if exists and fp.suffix.lower() == ".glb" and not magic:
            bad_magic += 1

        flags = []
        if dup_id:
            flags.append("DUP_ID")
        if dup_url:
            flags.append("DUP_URL")
        flag_s = ",".join(flags)

        print(
            f"{aid:<40} {str(exists):<6} {sz/1024/1024:>8.2f}   {str(magic):<6} {url} {flag_s}"
        )

    print("-" * 120)
    print(f"MANIFEST ASSETS: {len(assets)}")
    print(f"FOUND GLBs: {len(assets) - missing}")
    print(f"MISSING GLBs: {missing}")
    print(f"BAD GLB MAGIC: {bad_magic}")
    print(f"DUPLICATE IDS: {len(assets) - len(ids)}")
    print(f"DUPLICATE URLS: {len(assets) - len(urls)}")
    print(f"TOTAL SIZE MB: {total_bytes/1024/1024:.3f}")
    print(f"LARGEST FILE: {largest[0]} ({largest[1]/1024/1024:.3f} MB)")

    if missing or bad_magic:
        return 1
    print("WEB PACKAGE READY = True")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
