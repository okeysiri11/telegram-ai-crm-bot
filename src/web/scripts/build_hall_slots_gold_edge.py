#!/usr/bin/env python3
"""Build-time gold EDGE for the three GOLD cabinets + three real chairs.

Source of truth: hall.jpg visible pixels only.
Does not rewrite hall.jpg or hall-slots-foreground.png.
Does not draw synthetic chairs / legs / rings.
Does not emit clip-rectangle contours.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
HALL = ROOT / "public/assets/casino/lobby/hall.jpg"
OUT = ROOT / "public/assets/casino/lobby/hall-slots-gold-edge.png"

# Body seed windows (tight). Crowns use separate ROIs so bar bottles are excluded.
MACHINES = (
    (1278, 518, 1362, 768),
    (1400, 512, 1490, 752),
    (1524, 512, 1600, 734),
)

# Crown ROIs: just the rounded GOLD arch. Largest warm component only.
CROWNS = (
    (1286, 438, 1360, 562),
    (1406, 428, 1484, 558),
    (1528, 468, 1600, 572),
)

# Photographic chair windows (backrest + seat). Below seat_cut_y: footring glints only.
CHAIR_WINDOWS = (
    (1276, 668, 1346, 880, 776),
    (1398, 652, 1470, 858, 758),
    (1518, 648, 1590, 832, 740),
)

GOLD_RGB = (247, 200, 90)  # #F7C85A
CHAIR_STRENGTH = 0.65


def is_gold(r: int, g: int, b: int) -> bool:
    return r > 145 and g > 95 and (r - b) > 38 and (g - b) > 12 and r >= g - 15


def is_screen(r: int, g: int, b: int) -> bool:
    return r > 175 and g > 150 and b > 120 and (r + g + b) > 480


def is_warm_glint(r: int, g: int, b: int) -> bool:
    return r > 78 and g > 40 and (r - b) > 30 and (g - b) > 8 and (r + g + b) < 400


def is_crown_warm(r: int, g: int, b: int) -> bool:
    """Bronze/gold arch of the physical crown — looser than cabinet gold."""
    return r > 88 and g > 42 and (r - b) > 22 and (g - b) > 4


def lum(r: int, g: int, b: int) -> float:
    return 0.299 * r + 0.587 * g + 0.114 * b


def fill_holes_inside_box(mask: Image.Image, box: tuple[int, int, int, int]) -> None:
    """Fill interior holes. Pixels connected to the box border stay empty."""
    left, top, right, bottom = box
    mp = mask.load()
    w, h = mask.size
    right = min(right, w)
    bottom = min(bottom, h)

    visited = set()
    q: deque[tuple[int, int]] = deque()

    def consider(x: int, y: int) -> None:
        if x < left or x >= right or y < top or y >= bottom:
            return
        if (x, y) in visited:
            return
        if mp[x, y] >= 80:
            return
        visited.add((x, y))
        q.append((x, y))

    for x in range(left, right):
        consider(x, top)
        consider(x, bottom - 1)
    for y in range(top, bottom):
        consider(left, y)
        consider(right - 1, y)

    while q:
        x, y = q.popleft()
        consider(x - 1, y)
        consider(x + 1, y)
        consider(x, y - 1)
        consider(x, y + 1)

    for y in range(top, bottom):
        for x in range(left, right):
            if (x, y) not in visited and mp[x, y] < 80:
                mp[x, y] = 255


def largest_component(mask: Image.Image, box: tuple[int, int, int, int], min_size: int = 80) -> Image.Image:
    left, top, right, bottom = box
    mp = mask.load()
    w, h = mask.size
    right, bottom = min(right, w), min(bottom, h)
    seen: set[tuple[int, int]] = set()
    best: list[tuple[int, int]] = []
    for y in range(top, bottom):
        for x in range(left, right):
            if (x, y) in seen or mp[x, y] < 80:
                continue
            q = deque([(x, y)])
            seen.add((x, y))
            cells = [(x, y)]
            while q:
                cx, cy = q.popleft()
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if nx < left or nx >= right or ny < top or ny >= bottom:
                        continue
                    if (nx, ny) in seen or mp[nx, ny] < 80:
                        continue
                    seen.add((nx, ny))
                    q.append((nx, ny))
                    cells.append((nx, ny))
            if len(cells) > len(best):
                best = cells
    out = Image.new("L", (w, h), 0)
    if len(best) >= min_size:
        op = out.load()
        for x, y in best:
            op[x, y] = 255
    return out


def machine_fill(hall: Image.Image) -> Image.Image:
    """Crown = largest warm component in crown ROI. Body = gold/screen trim only."""
    w, h = hall.size
    px = hall.load()

    crown_seed = Image.new("L", (w, h), 0)
    csp = crown_seed.load()
    for left, top, right, bottom in CROWNS:
        for y in range(top, min(bottom, h)):
            for x in range(left, min(right, w)):
                r, g, b = px[x, y]
                if is_crown_warm(r, g, b) or is_gold(r, g, b):
                    csp[x, y] = 255
    crowns = Image.new("L", (w, h), 0)
    for box in CROWNS:
        part = largest_component(crown_seed, box, min_size=120)
        fill_holes_inside_box(part, box)
        crowns = ImageChops.lighter(crowns, part)

    body = Image.new("L", (w, h), 0)
    bp = body.load()
    for left, top, right, bottom in MACHINES:
        for y in range(top, min(bottom, h)):
            for x in range(left, min(right, w)):
                r, g, b = px[x, y]
                if is_gold(r, g, b) or is_screen(r, g, b):
                    bp[x, y] = 255
    body = body.filter(ImageFilter.MaxFilter(3))
    filled = ImageChops.lighter(crowns, body)
    for box in MACHINES:
        fill_holes_inside_box(filled, box)
    return filled


def chair_visible_edges(hall: Image.Image, machines: Image.Image) -> Image.Image:
    """Outer contour of visible dark chair pixels + footring glints. No invented legs."""
    w, h = hall.size
    px = hall.load()
    mp = machines.load()
    body = Image.new("L", (w, h), 0)
    bp = body.load()
    glints = Image.new("L", (w, h), 0)
    gp = glints.load()

    for left, top, right, bottom, seat_cut in CHAIR_WINDOWS:
        for y in range(top, min(bottom, h)):
            for x in range(left, min(right, w)):
                if mp[x, y] >= 80:
                    continue
                r, g, b = px[x, y]
                L = lum(r, g, b)
                adj_machine = False
                adj_bright = False
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if not (0 <= nx < w and 0 <= ny < h):
                        continue
                    if mp[nx, ny] >= 80:
                        adj_machine = True
                    if lum(*px[nx, ny]) >= 72:
                        adj_bright = True
                # Boundary only — never the seat interior gradient.
                if y <= seat_cut and L < 46 and (adj_machine or adj_bright):
                    bp[x, y] = 255
                if is_warm_glint(r, g, b) and y > seat_cut:
                    gp[x, y] = 255

    edges = Image.new("L", (w, h), 0)
    for box in CHAIR_WINDOWS:
        part = largest_component(body, box[:4], min_size=20)
        edges = ImageChops.lighter(edges, part)
    return ImageChops.lighter(edges, glints)


def outer_edge(mask: Image.Image, erode: int = 3) -> Image.Image:
    binary = mask.point(lambda a: 255 if a >= 80 else 0)
    return ImageChops.subtract(binary, binary.filter(ImageFilter.MinFilter(erode)))


def compose_gold(machine_edge: Image.Image, chair_edge: Image.Image) -> Image.Image:
    m_halo = machine_edge.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    m_a = ImageChops.lighter(machine_edge, m_halo.point(lambda a: int(a * 0.34)))

    c_halo = chair_edge.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.65))
    c_core = ImageChops.lighter(chair_edge, c_halo.point(lambda a: int(a * 0.28)))
    c_a = c_core.point(lambda a: int(a * CHAIR_STRENGTH))

    gold_a = ImageChops.lighter(m_a, c_a)
    img = Image.new("RGBA", machine_edge.size, (*GOLD_RGB, 0))
    img.putalpha(gold_a)
    return img


def region_counts(alpha: Image.Image) -> dict[str, int]:
    ap = alpha.load()
    counts = {"m1": 0, "m2": 0, "m3": 0, "c1": 0, "c2": 0, "c3": 0}

    def add(box: tuple[int, int, int, int], key: str) -> None:
        l, t, r, b = box
        for y in range(t, b):
            for x in range(l, r):
                if ap[x, y] > 20:
                    counts[key] += 1

    add((1276, 448, 1364, 620), "m1")
    add((1398, 436, 1492, 610), "m2")
    add((1522, 428, 1600, 600), "m3")
    add((1274, 662, 1348, 884), "c1")
    add((1396, 644, 1472, 864), "c2")
    add((1516, 626, 1592, 838), "c3")
    return counts


def build() -> dict:
    hall = Image.open(HALL).convert("RGB")
    if hall.size != (1600, 1066):
        raise SystemExit(f"unexpected hall size {hall.size}")

    machines = machine_fill(hall)
    m_edge = outer_edge(machines, 3)
    chairs = chair_visible_edges(hall, machines)
    img = compose_gold(m_edge, chairs)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG")

    alpha = img.split()[-1]
    hist = alpha.histogram()
    trans = sum(hist[:8])
    total = 1600 * 1066
    counts = region_counts(alpha)
    return {
        "out": str(OUT),
        "size": "1600x1066",
        "transparent_percent": round(100.0 * trans / total, 2),
        **{f"edge_px_{k}": v for k, v in counts.items()},
    }


if __name__ == "__main__":
    info = build()
    for k, v in info.items():
        print(f"{k}={v}")
    if info["transparent_percent"] < 90:
        raise SystemExit("FAIL: gold edge is too opaque")
    if any(info[f"edge_px_{k}"] < 80 for k in ("m1", "m2", "m3")):
        raise SystemExit("FAIL: a machine crown/body has almost no edge")
    if any(info[f"edge_px_{k}"] < 30 for k in ("c1", "c2", "c3")):
        raise SystemExit("FAIL: a chair window has almost no visible edge")
