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

/** Mask roles: photographic lift only. Never painted as geometry. */
export type HallVisualRole = "object" | "sign" | "lamp" | "pulse";

export type HallVisual = {
  polygon: HallPoint[];
  role?: HallVisualRole;
};

export type HallZone = {
  id: HallZoneId;
  label: string;
  sublabel: string;
  cta: string;
  route: string;
  /** Pointer hit polygons in normalized image percent (0–100). Invisible. */
  polygons: HallPoint[][];
  /** Object-locked illumination masks. Defaults to hit polygons. */
  visuals?: HallVisual[];
  objects: string[];
  focus: { x: number; y: number };
  /** Tooltip anchor in image percent; must not cover the primary object. */
  tooltip: { x: number; y: number; align: HallTooltipAlign };
  zIndex: number;
};

/**
 * Object masks for hall.jpg (1600×1066).
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
        [4.2, 28.8],
        [25.2, 27.4],
        [26.0, 38.4],
        [5.0, 39.8],
      ],
      [
        [0.6, 50.5],
        [21.5, 47.6],
        [34.2, 54.2],
        [36.2, 70.0],
        [31.8, 99.0],
        [0.5, 99.0],
        [0.5, 71.0],
      ],
      [
        [16.2, 44.8],
        [24.2, 44.0],
        [25.6, 57.0],
        [17.8, 58.0],
      ],
    ],
    visuals: [
      {
        role: "sign",
        polygon: [
          [4.6, 29.4],
          [24.6, 28.0],
          [25.2, 37.2],
          [5.2, 38.6],
        ],
      },
      {
        role: "lamp",
        polygon: [
          [16.8, 45.2],
          [23.8, 44.6],
          [25.0, 56.8],
          [18.0, 57.6],
        ],
      },
      {
        role: "object",
        polygon: [
          [1.4, 68.5],
          [8.6, 60.8],
          [14.8, 63.4],
          [16.2, 78.6],
          [11.4, 92.4],
          [2.2, 94.8],
          [0.8, 80.2],
        ],
      },
      {
        role: "object",
        polygon: [
          [7.2, 56.8],
          [21.6, 52.4],
          [33.4, 59.6],
          [34.8, 73.2],
          [29.6, 92.8],
          [8.8, 97.6],
          [3.6, 78.4],
        ],
      },
      {
        role: "object",
        polygon: [
          [18.8, 48.6],
          [31.2, 47.2],
          [33.6, 58.8],
          [22.4, 61.2],
        ],
      },
    ],
    focus: { x: 16, y: 68 },
    tooltip: { x: 37.5, y: 48, align: "right" },
    zIndex: 4,
  },
  {
    id: "blackjack",
    label: "BLACKJACK",
    sublabel: "SALON",
    cta: "ВОЙТИ",
    route: "/casino/blackjack",
    objects: ["sign", "table", "lamp"],
    polygons: [
      [
        [7.0, 12.8],
        [27.0, 11.4],
        [28.8, 18.8],
        [8.2, 20.4],
      ],
      [
        [8.2, 19.2],
        [27.6, 17.6],
        [29.0, 34.6],
        [25.4, 42.4],
        [10.0, 43.6],
        [7.6, 31.6],
      ],
    ],
    visuals: [
      {
        role: "sign",
        polygon: [
          [7.4, 13.2],
          [26.6, 11.8],
          [27.8, 18.0],
          [8.4, 19.4],
        ],
      },
      {
        role: "object",
        polygon: [
          [10.2, 22.8],
          [26.2, 21.2],
          [27.6, 33.4],
          [24.2, 41.0],
          [11.8, 42.2],
          [9.4, 31.6],
        ],
      },
      {
        role: "lamp",
        polygon: [
          [15.4, 26.8],
          [18.8, 26.4],
          [19.2, 31.6],
          [15.8, 32.0],
        ],
      },
    ],
    focus: { x: 18, y: 28 },
    tooltip: { x: 18, y: 10.2, align: "above" },
    zIndex: 3,
  },
  {
    id: "poker",
    label: "POKER ROOM",
    sublabel: "ODESSA PRIME",
    cta: "ВОЙТИ В ПОКЕР",
    route: "/casino/poker",
    objects: ["sign", "doorway", "curtains"],
    polygons: [
      [
        [45.6, 12.8],
        [55.8, 12.0],
        [56.4, 20.8],
        [46.0, 21.6],
      ],
      [
        [46.4, 20.4],
        [55.8, 19.6],
        [56.2, 36.2],
        [46.2, 37.0],
      ],
      [
        [54.4, 15.6],
        [62.2, 14.8],
        [62.6, 21.0],
        [54.8, 21.8],
      ],
    ],
    visuals: [
      {
        role: "sign",
        polygon: [
          [45.8, 13.2],
          [55.6, 12.4],
          [56.0, 18.6],
          [46.2, 19.4],
        ],
      },
      {
        role: "sign",
        polygon: [
          [54.8, 16.0],
          [61.8, 15.2],
          [62.2, 20.4],
          [55.2, 21.2],
        ],
      },
      {
        role: "object",
        polygon: [
          [46.8, 19.8],
          [55.4, 19.0],
          [55.8, 35.4],
          [47.0, 36.2],
        ],
      },
      {
        role: "object",
        polygon: [
          [45.6, 22.4],
          [47.4, 21.8],
          [47.8, 35.6],
          [45.4, 36.0],
        ],
      },
      {
        role: "object",
        polygon: [
          [54.8, 21.4],
          [56.8, 20.8],
          [57.0, 34.8],
          [54.6, 35.4],
        ],
      },
    ],
    focus: { x: 51, y: 26 },
    tooltip: { x: 51, y: 11.6, align: "above" },
    zIndex: 1,
  },
  {
    id: "restaurant",
    label: "РЕСТОРАН",
    sublabel: "ODESSA PRIME",
    cta: "ПЕРЕЙТИ В РЕСТОРАН",
    route: "/casino/restaurant",
    objects: ["sign", "doorway", "tables", "lamps"],
    polygons: [
      [
        [57.0, 13.8],
        [68.8, 13.0],
        [69.2, 19.2],
        [57.4, 20.0],
      ],
      [
        [57.2, 19.6],
        [70.2, 18.6],
        [71.4, 36.2],
        [56.6, 37.2],
      ],
    ],
    visuals: [
      {
        role: "sign",
        polygon: [
          [57.4, 14.4],
          [68.4, 13.6],
          [68.8, 18.6],
          [57.8, 19.4],
        ],
      },
      {
        role: "object",
        polygon: [
          [58.0, 19.8],
          [69.0, 18.8],
          [69.6, 24.6],
          [58.4, 25.4],
        ],
      },
      {
        role: "object",
        polygon: [
          [58.2, 24.8],
          [69.8, 23.8],
          [70.8, 35.0],
          [57.6, 36.0],
        ],
      },
      {
        role: "lamp",
        polygon: [
          [60.4, 27.2],
          [63.2, 26.8],
          [63.6, 31.0],
          [60.8, 31.4],
        ],
      },
      {
        role: "lamp",
        polygon: [
          [65.0, 27.8],
          [67.8, 27.4],
          [68.2, 31.6],
          [65.4, 32.0],
        ],
      },
    ],
    focus: { x: 63, y: 28 },
    tooltip: { x: 54.2, y: 16.4, align: "left" },
    zIndex: 1,
  },
  {
    id: "bar",
    label: "БАР",
    sublabel: "ODESSA PRIME",
    cta: "ПЕРЕЙТИ В БАР",
    route: "/casino/bar",
    objects: ["sign", "shelves", "bottles", "counter"],
    polygons: [
      [
        [77.6, 4.8],
        [88.6, 3.8],
        [89.0, 8.6],
        [78.0, 9.6],
      ],
      [
        [77.2, 8.8],
        [92.6, 7.0],
        [93.4, 26.8],
        [78.0, 28.2],
      ],
    ],
    visuals: [
      {
        role: "sign",
        polygon: [
          [78.0, 5.0],
          [88.2, 4.0],
          [88.6, 8.4],
          [78.4, 9.4],
        ],
      },
      {
        role: "object",
        polygon: [
          [78.6, 9.6],
          [91.8, 8.0],
          [92.6, 22.4],
          [79.4, 23.8],
        ],
      },
      {
        role: "pulse",
        polygon: [
          [81.6, 11.6],
          [90.2, 10.4],
          [90.8, 20.8],
          [82.4, 21.8],
        ],
      },
      {
        role: "object",
        polygon: [
          [78.4, 22.6],
          [92.4, 21.2],
          [93.0, 27.0],
          [78.8, 28.0],
        ],
      },
    ],
    focus: { x: 85, y: 16 },
    tooltip: { x: 74.2, y: 9.2, align: "left" },
    zIndex: 2,
  },
  {
    id: "slots",
    label: "ИГРАТЬ В АВТОМАТЫ",
    sublabel: "SLOTS",
    cta: "ИГРАТЬ",
    route: "/casino/slots",
    objects: ["machine-1", "machine-2", "machine-3", "stools"],
    polygons: [
      [
        [58.6, 49.8],
        [67.8, 48.4],
        [69.0, 86.8],
        [57.4, 90.0],
      ],
      [
        [67.6, 48.6],
        [77.6, 47.2],
        [79.0, 84.2],
        [67.2, 87.0],
      ],
      [
        [77.2, 47.0],
        [90.8, 45.2],
        [93.6, 80.8],
        [77.4, 84.4],
      ],
    ],
    visuals: [
      {
        role: "object",
        polygon: [
          [59.0, 54.6],
          [62.8, 49.4],
          [66.6, 53.4],
          [67.4, 78.4],
          [65.6, 85.6],
          [58.8, 87.2],
          [57.8, 79.6],
        ],
      },
      {
        role: "object",
        polygon: [
          [67.2, 53.2],
          [71.8, 48.0],
          [76.8, 51.6],
          [77.6, 76.8],
          [75.8, 84.0],
          [66.8, 85.6],
          [66.2, 78.0],
        ],
      },
      {
        role: "object",
        polygon: [
          [77.0, 51.4],
          [83.6, 45.8],
          [90.0, 49.4],
          [91.4, 74.8],
          [89.4, 81.4],
          [77.2, 83.0],
          [76.4, 75.6],
        ],
      },
      {
        role: "object",
        polygon: [
          [59.4, 84.8],
          [64.8, 83.6],
          [65.2, 89.2],
          [59.0, 90.4],
        ],
      },
      {
        role: "object",
        polygon: [
          [68.4, 83.6],
          [74.2, 82.2],
          [74.6, 87.8],
          [68.0, 89.0],
        ],
      },
      {
        role: "object",
        polygon: [
          [79.0, 81.0],
          [86.8, 79.2],
          [87.4, 84.8],
          [78.6, 86.2],
        ],
      },
      {
        role: "pulse",
        polygon: [
          [61.0, 56.2],
          [65.4, 55.4],
          [65.8, 62.4],
          [61.4, 63.2],
        ],
      },
      {
        role: "pulse",
        polygon: [
          [69.8, 54.8],
          [74.8, 54.0],
          [75.2, 61.0],
          [70.2, 61.8],
        ],
      },
      {
        role: "pulse",
        polygon: [
          [80.4, 53.2],
          [87.2, 52.2],
          [87.6, 59.4],
          [80.8, 60.4],
        ],
      },
    ],
    focus: { x: 76, y: 66 },
    tooltip: { x: 74, y: 43.2, align: "above" },
    zIndex: 5,
  },
];

export function zoneVisuals(zone: HallZone): HallVisual[] {
  if (zone.visuals?.length) return zone.visuals;
  return zone.polygons.map((polygon) => ({ polygon, role: "object" as const }));
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
    if (!zoneVisuals(zone).length) errors.push(`visuals-missing:${zone.id}`);
    for (const polygon of [...zone.polygons, ...zoneVisuals(zone).map((v) => v.polygon)]) {
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
  const slotObjects = zoneVisuals(slots ?? HALL_ZONES[5]).filter((v) => (v.role ?? "object") === "object");
  if (slotObjects.length < 3) errors.push("slots-cabinet-visuals");
  return errors;
}
