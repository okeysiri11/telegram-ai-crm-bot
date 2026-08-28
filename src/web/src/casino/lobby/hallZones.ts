import { CASINO_ROUTES } from "../state/casinoRoutes";

/** Source hall artwork. Overlay coordinates are percent of this image (0–100). */
export const HALL_ART = {
  src: "/assets/casino/lobby/hall.jpg",
  width: 1600,
  height: 1066,
} as const;

/** Click focus then navigate. Keep inside 150–350ms. */
export const HALL_ENTER_MS = 200;

export type HallZoneId = "roulette" | "blackjack" | "poker" | "restaurant" | "bar" | "slots";

export type HallPoint = [number, number];

export type HallTooltipAlign = "above" | "below" | "left" | "right";

export type HallZone = {
  id: HallZoneId;
  label: string;
  sublabel: string;
  cta: string;
  route: string;
  /** Pointer hit polygons in normalized image percent (0–100). Invisible. */
  polygons: HallPoint[][];
  /** Visible glow traces; defaults to hit polygons when omitted. */
  visuals?: HallPoint[][];
  objects: string[];
  focus: { x: number; y: number };
  /** Tooltip anchor in image percent; must not cover the primary object. */
  tooltip: { x: number; y: number; align: HallTooltipAlign };
  zIndex: number;
};

/**
 * Object-based spatial zones for hall.jpg (1600×1066).
 * Tab order: Roulette → Blackjack → Poker → Restaurant → Bar → Slots.
 */
export const HALL_ZONES: HallZone[] = [
  {
    id: "roulette",
    label: "РУЛЕТКА",
    sublabel: "MONTE CARLO",
    cta: "ВОЙТИ В РУЛЕТКУ",
    route: CASINO_ROUTES.rouletteLive,
    objects: ["sign", "table", "lamp", "wheel"],
    polygons: [
      [
        [4.5, 29.5],
        [24.8, 28.0],
        [25.4, 37.8],
        [5.2, 39.4],
      ],
      [
        [0.8, 51.0],
        [22.0, 48.2],
        [33.5, 54.0],
        [35.8, 68.5],
        [31.5, 99.2],
        [0.6, 99.2],
        [0.6, 72.0],
      ],
      [
        [16.5, 45.5],
        [23.8, 44.8],
        [25.2, 56.5],
        [18.0, 57.8],
      ],
    ],
    focus: { x: 16, y: 68 },
    tooltip: { x: 36, y: 46, align: "right" },
    zIndex: 4,
  },
  {
    id: "blackjack",
    label: "BLACKJACK",
    sublabel: "SALON",
    cta: "ВОЙТИ",
    route: "/casino/blackjack",
    objects: ["sign", "arch", "table"],
    polygons: [
      [
        [7.2, 13.2],
        [26.8, 11.8],
        [28.6, 18.5],
        [8.4, 20.2],
      ],
      [
        [8.0, 19.5],
        [27.8, 17.8],
        [29.4, 34.0],
        [26.0, 42.8],
        [9.6, 44.2],
        [7.4, 32.0],
      ],
    ],
    focus: { x: 18, y: 28 },
    tooltip: { x: 18, y: 10.5, align: "above" },
    zIndex: 3,
  },
  {
    id: "poker",
    label: "POKER ROOM",
    sublabel: "ODESSA PRIME",
    cta: "ВОЙТИ В ПОКЕР",
    route: "/casino/poker",
    objects: ["sign", "doorway"],
    polygons: [
      [
        [46.8, 16.6],
        [54.2, 15.8],
        [54.8, 20.4],
        [47.2, 21.2],
      ],
      [
        [47.0, 20.6],
        [54.6, 19.8],
        [55.0, 34.8],
        [47.4, 35.8],
      ],
    ],
    focus: { x: 51, y: 26 },
    tooltip: { x: 51, y: 14.2, align: "above" },
    zIndex: 1,
  },
  {
    id: "restaurant",
    label: "РЕСТОРАН",
    sublabel: "RESTAURANT",
    cta: "ПЕРЕЙТИ В РЕСТОРАН",
    route: "/casino/restaurant",
    objects: ["sign", "tables"],
    polygons: [
      [
        [57.2, 14.4],
        [68.6, 13.6],
        [69.0, 18.8],
        [57.6, 19.6],
      ],
      [
        [56.8, 19.2],
        [69.8, 18.2],
        [71.2, 35.6],
        [56.2, 36.8],
      ],
    ],
    focus: { x: 63, y: 26 },
    tooltip: { x: 54.5, y: 16, align: "left" },
    zIndex: 1,
  },
  {
    id: "bar",
    label: "БАР",
    sublabel: "BAR",
    cta: "ПЕРЕЙТИ В БАР",
    route: "/casino/bar",
    objects: ["sign", "shelves"],
    polygons: [
      [
        [77.4, 3.6],
        [88.8, 2.6],
        [89.2, 7.8],
        [77.8, 8.8],
      ],
      [
        [76.6, 8.2],
        [92.4, 6.4],
        [93.6, 24.8],
        [77.8, 26.6],
      ],
    ],
    focus: { x: 85, y: 16 },
    tooltip: { x: 74, y: 8, align: "left" },
    zIndex: 2,
  },
  {
    id: "slots",
    label: "ИГРАТЬ В АВТОМАТЫ",
    sublabel: "SLOTS",
    cta: "ИГРАТЬ",
    route: "/casino/slots",
    objects: ["machine-1", "machine-2", "machine-3"],
    polygons: [
      [
        [58.8, 50.5],
        [67.6, 49.0],
        [69.2, 86.5],
        [57.6, 90.2],
      ],
      [
        [67.6, 49.0],
        [77.4, 47.6],
        [79.2, 84.0],
        [67.4, 87.0],
      ],
      [
        [77.4, 47.6],
        [90.6, 45.8],
        [93.8, 80.5],
        [77.6, 84.2],
      ],
    ],
    focus: { x: 76, y: 68 },
    tooltip: { x: 74, y: 43.5, align: "above" },
    zIndex: 5,
  },
];

export function zoneVisuals(zone: HallZone): HallPoint[][] {
  return zone.visuals ?? zone.polygons;
}

export function hallZoneById(id: string | null | undefined): HallZone | undefined {
  if (!id) return undefined;
  return HALL_ZONES.find((z) => z.id === id);
}

export function polygonPoints(polygon: HallPoint[]): string {
  return polygon.map(([x, y]) => `${x},${y}`).join(" ");
}

export function clampTooltip(x: number, y: number): { x: number; y: number } {
  return {
    x: Math.min(92, Math.max(8, x)),
    y: Math.min(90, Math.max(8, y)),
  };
}

export function validateHallZones(zones: HallZone[] = HALL_ZONES): string[] {
  const errors: string[] = [];
  const seen = new Set<string>();
  for (const zone of zones) {
    if (seen.has(zone.id)) errors.push(`duplicate:${zone.id}`);
    seen.add(zone.id);
    if (!zone.route.startsWith("/casino")) errors.push(`route:${zone.id}`);
    if (!zone.polygons.length) errors.push(`polygons-missing:${zone.id}`);
    if (!zone.objects.length) errors.push(`objects:${zone.id}`);
    for (const polygon of [...zone.polygons, ...(zone.visuals ?? [])]) {
      if (polygon.length < 3) errors.push(`polygon-short:${zone.id}`);
      for (const [x, y] of polygon) {
        if (x < 0 || x > 100 || y < 0 || y > 100) errors.push(`bounds:${zone.id}`);
      }
    }
    if (zone.tooltip.x < 0 || zone.tooltip.x > 100 || zone.tooltip.y < 0 || zone.tooltip.y > 100) {
      errors.push(`tooltip:${zone.id}`);
    }
  }
  if (seen.size !== 6) errors.push("count");
  const roulette = zones.find((z) => z.id === "roulette");
  const slots = zones.find((z) => z.id === "slots");
  if ((roulette?.polygons.length ?? 0) < 2) errors.push("roulette-multipolygon");
  if ((slots?.polygons.length ?? 0) < 2) errors.push("slots-multipolygon");
  return errors;
}
