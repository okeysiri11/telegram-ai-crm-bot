import { CASINO_ROUTES } from "../state/casinoRoutes";

/** Source hall artwork. Overlay coordinates are percent of this image (0–100). */
export const HALL_ART = {
  src: "/assets/casino/lobby/hall.jpg",
  width: 1600,
  height: 1066,
} as const;

export const HALL_ENTER_MS = 420;

export type HallZoneId = "roulette" | "blackjack" | "poker" | "restaurant" | "bar" | "slots";

export type HallPoint = [number, number];

export type HallZone = {
  id: HallZoneId;
  label: string;
  sublabel: string;
  cta: string;
  route: string;
  /** Clockwise polygon in normalized image percent (0–100). */
  polygon: HallPoint[];
  /** Camera target in image percent. */
  focus: { x: number; y: number };
  labelAt: { x: number; y: number };
  zIndex: number;
};

/**
 * Spatial zones mapped to visible objects in hall.jpg.
 * Array order is keyboard tab order:
 * Roulette → Blackjack → Poker → Restaurant → Bar → Slots.
 */
export const HALL_ZONES: HallZone[] = [
  {
    id: "roulette",
    label: "РУЛЕТКА",
    sublabel: "MONTE CARLO",
    cta: "ВОЙТИ В РУЛЕТКУ",
    route: CASINO_ROUTES.rouletteLive,
    polygon: [
      [0, 34],
      [21, 30],
      [38, 38],
      [42, 58],
      [36, 100],
      [0, 100],
    ],
    focus: { x: 18, y: 70 },
    labelAt: { x: 22, y: 50 },
    zIndex: 4,
  },
  {
    id: "blackjack",
    label: "BLACKJACK SALON",
    sublabel: "SALON",
    cta: "ВОЙТИ",
    route: "/casino/blackjack",
    polygon: [
      [6, 13],
      [32, 11],
      [35, 34],
      [29, 44],
      [7, 46],
    ],
    focus: { x: 20, y: 30 },
    labelAt: { x: 20, y: 9 },
    zIndex: 3,
  },
  {
    id: "poker",
    label: "POKER ROOM",
    sublabel: "POKER",
    cta: "ВОЙТИ В ПОКЕР",
    route: "/casino/poker",
    polygon: [
      [39, 16],
      [54, 15],
      [55, 40],
      [40, 42],
    ],
    focus: { x: 47, y: 28 },
    labelAt: { x: 47, y: 11 },
    zIndex: 1,
  },
  {
    id: "restaurant",
    label: "РЕСТОРАН",
    sublabel: "RESTAURANT",
    cta: "ПЕРЕЙТИ В РЕСТОРАН",
    route: "/casino/restaurant",
    polygon: [
      [54, 14],
      [72, 13],
      [74, 38],
      [55, 40],
    ],
    focus: { x: 64, y: 26 },
    labelAt: { x: 64, y: 10 },
    zIndex: 1,
  },
  {
    id: "bar",
    label: "БАР",
    sublabel: "BAR",
    cta: "ПЕРЕЙТИ В БАР",
    route: "/casino/bar",
    polygon: [
      [72, 4],
      [96, 3],
      [98, 32],
      [74, 36],
    ],
    focus: { x: 84, y: 18 },
    labelAt: { x: 84, y: 4 },
    zIndex: 2,
  },
  {
    id: "slots",
    label: "ИГРАТЬ В АВТОМАТЫ",
    sublabel: "SLOTS",
    cta: "ИГРАТЬ",
    route: "/casino/slots",
    polygon: [
      [66, 48],
      [100, 42],
      [100, 100],
      [64, 100],
    ],
    focus: { x: 84, y: 72 },
    labelAt: { x: 78, y: 44 },
    zIndex: 5,
  },
];

export function hallZoneById(id: string | null | undefined): HallZone | undefined {
  if (!id) return undefined;
  return HALL_ZONES.find((z) => z.id === id);
}

export function polygonPoints(polygon: HallPoint[]): string {
  return polygon.map(([x, y]) => `${x},${y}`).join(" ");
}

export function polygonClipPath(polygon: HallPoint[]): string {
  return `polygon(${polygon.map(([x, y]) => `${x}% ${y}%`).join(", ")})`;
}

export function validateHallZones(zones: HallZone[] = HALL_ZONES): string[] {
  const errors: string[] = [];
  const seen = new Set<string>();
  for (const zone of zones) {
    if (seen.has(zone.id)) errors.push(`duplicate:${zone.id}`);
    seen.add(zone.id);
    if (!zone.route.startsWith("/casino")) errors.push(`route:${zone.id}`);
    if (zone.polygon.length < 3) errors.push(`polygon-short:${zone.id}`);
    for (const [x, y] of zone.polygon) {
      if (x < 0 || x > 100 || y < 0 || y > 100) errors.push(`bounds:${zone.id}`);
    }
    if (zone.focus.x < 0 || zone.focus.x > 100 || zone.focus.y < 0 || zone.focus.y > 100) {
      errors.push(`focus:${zone.id}`);
    }
  }
  if (seen.size !== 6) errors.push("count");
  return errors;
}
