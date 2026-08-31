#!/usr/bin/env python3
"""Cut 3 GOLD cabinets + 3 chairs from hall.jpg onto a transparent PNG.

Machines: seed (GOLD + 777 screens) inside per-cabinet boxes, then dilate
into the dark cabinet. Chairs: backrest/seat ellipses plus thin photographic
legs; footring holes stay on the chair layer only.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat

ROOT = Path(__file__).resolve().parents[1]
HALL = ROOT / "public/assets/casino/lobby/hall.jpg"
OUT = ROOT / "public/assets/casino/lobby/hall-slots-foreground.png"

# (left, top, right, bottom) in hall pixels — tight, no neighbor overlap.
MACHINES = (
    (1276, 508, 1362, 776),
    (1400, 494, 1490, 758),
    (1524, 480, 1599, 740),
)

CHAIRS = (
    # bx, by, brx, bry, seat_y, srx, sry, ring_y, foot_y
    (1306, 704, 38, 44, 762, 33, 13, 832, 880),
    (1428, 688, 39, 42, 744, 34, 12, 812, 858),
    (1544, 670, 35, 38, 722, 30, 11, 788, 832),
)


def is_gold(r: int, g: int, b: int) -> bool:
    return r > 145 and g > 95 and (r - b) > 38 and (g - b) > 12 and r >= g - 15


def is_screen(r: int, g: int, b: int) -> bool:
    return r > 175 and g > 150 and b > 120 and (r + g + b) > 480


def machine_seed_mask(hall: Image.Image) -> Image.Image:
    w, h = hall.size
    px = hall.load()
    seed = Image.new("L", (w, h), 0)
    sp = seed.load()
    for left, top, right, bottom in MACHINES:
        for y in range(top, min(bottom, h)):
            for x in range(left, min(right, w)):
                if y < top + 6:
                    continue
                r, g, b = px[x, y]
                if is_gold(r, g, b) or is_screen(r, g, b):
                    sp[x, y] = 255
    # Fill the dark cabinet around those seeds without jumping to the bar.
    grown = seed.filter(ImageFilter.MaxFilter(5))
    clip = Image.new("L", (w, h), 0)
    cd = ImageDraw.Draw(clip)
    for left, top, right, bottom in MACHINES:
        cd.rounded_rectangle((left, top, right - 1, bottom - 1), radius=18, fill=255)
    grown = ImageChops.multiply(grown, clip)
    # Keep original seeds full-strength, dilation slightly softer.
    return ImageChops.lighter(seed, grown)


def chair_mask(size: tuple[int, int]) -> Image.Image:
    img = Image.new("L", size, 0)
    d = ImageDraw.Draw(img)
    for bx, by, brx, bry, seat_y, srx, sry, ring_y, foot_y in CHAIRS:
        d.ellipse((bx - brx, by - bry, bx + brx, by + bry), fill=255)
        d.ellipse((bx - srx, seat_y - sry, bx + srx, seat_y + sry), fill=255)
        stem = 3.2
        d.polygon(
            [(bx - stem, seat_y), (bx + stem, seat_y), (bx + stem * 0.5, ring_y), (bx - stem * 0.5, ring_y)],
            fill=255,
        )
        for dx in (-0.7, -0.25, 0.25, 0.7):
            top_x = bx + dx * srx * 0.3
            bot_x = bx + dx * srx * 1.0
            d.line((top_x, ring_y - 4, bot_x, foot_y), fill=255, width=3)
        rx, ry = srx * 0.88, 9
        d.ellipse((bx - rx, ring_y - ry, bx + rx, ring_y + ry), outline=255, width=4)
    return img


def build() -> dict:
    hall = Image.open(HALL).convert("RGB")
    w, h = hall.size
    if (w, h) != (1600, 1066):
        raise SystemExit(f"unexpected hall size {w}x{h}")

    machines = machine_seed_mask(hall)
    chairs = chair_mask((w, h))
    mask = ImageChops.lighter(machines, chairs)
    mask = mask.filter(ImageFilter.GaussianBlur(0.4))
    mask = mask.point(lambda a: 255 if a >= 72 else (int(a * 1.25) if a > 18 else 0))

    fg = hall.convert("RGBA")
    fg.putalpha(mask)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fg.save(OUT, "PNG")

    hist = mask.histogram()
    trans = sum(hist[:8])
    total = w * h
    return {
        "source": f"{w}x{h}",
        "out": str(OUT),
        "has_alpha": True,
        "transparent_percent": round(100.0 * trans / total, 2),
        "opaque_pixels": total - trans,
        "bbox": mask.getbbox(),
        "mean_alpha": round(float(ImageStat.Stat(mask).mean[0]), 3),
    }


if __name__ == "__main__":
    info = build()
    for k, v in info.items():
        print(f"{k}={v}")
    if info["transparent_percent"] < 40:
        raise SystemExit("FAIL: PNG is too opaque")
    if info["transparent_percent"] > 99.2:
        raise SystemExit("FAIL: PNG has almost no objects")
