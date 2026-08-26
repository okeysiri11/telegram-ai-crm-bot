export type LobbyHotspot = {
  id: "roulette" | "blackjack" | "slots" | "poker" | "vip" | "bar" | "restaurant";
  label: string;
  venue: string;
  detail: string;
  cta: string;
  to: string;
  x: string;
  y: string;
  w: string;
  h: string;
  map: { x: number; y: number; w: number; h: number };
};

/** Spatial hall placement. Occupancy is omitted unless a live API value exists. */
export const LOBBY_HOTSPOTS: LobbyHotspot[] = [
  {
    id: "vip",
    label: "VIP",
    venue: "Monaco Private",
    detail: "PLAY",
    cta: "ВОЙТИ",
    to: "/casino/vip",
    x: "4%",
    y: "8%",
    w: "18%",
    h: "22%",
    map: { x: 40, y: 36, w: 170, h: 110 },
  },
  {
    id: "restaurant",
    label: "РЕСТОРАН",
    venue: "Odessa Dining",
    detail: "PLAY",
    cta: "ВОЙТИ",
    to: "/casino/restaurant",
    x: "26%",
    y: "6%",
    w: "22%",
    h: "20%",
    map: { x: 250, y: 28, w: 220, h: 100 },
  },
  {
    id: "poker",
    label: "ПОКЕР",
    venue: "Приморский Felt",
    detail: "PLAY",
    cta: "ВОЙТИ",
    to: "/casino/poker",
    x: "51%",
    y: "8%",
    w: "20%",
    h: "20%",
    map: { x: 500, y: 36, w: 190, h: 110 },
  },
  {
    id: "bar",
    label: "БАР",
    venue: "Black Sea Night",
    detail: "PLAY",
    cta: "ВОЙТИ",
    to: "/casino/bar",
    x: "76%",
    y: "8%",
    w: "20%",
    h: "22%",
    map: { x: 730, y: 32, w: 200, h: 114 },
  },
  {
    id: "roulette",
    label: "РУЛЕТКА",
    venue: "Roulette Royale 1",
    detail: "Ставки 10–5 000 PLAY",
    cta: "ВОЙТИ",
    to: "/casino/roulette/royale-1",
    x: "8%",
    y: "42%",
    w: "28%",
    h: "38%",
    map: { x: 70, y: 280, w: 280, h: 200 },
  },
  {
    id: "blackjack",
    label: "BLACKJACK",
    venue: "Salon Marina",
    detail: "PLAY",
    cta: "ВОЙТИ",
    to: "/casino/blackjack",
    x: "40%",
    y: "40%",
    w: "24%",
    h: "40%",
    map: { x: 380, y: 270, w: 240, h: 210 },
  },
  {
    id: "slots",
    label: "АВТОМАТЫ",
    venue: "Odessa Gold",
    detail: "SLOTS · PLAY",
    cta: "ИГРАТЬ",
    to: "/casino/slots",
    x: "68%",
    y: "42%",
    w: "26%",
    h: "38%",
    map: { x: 660, y: 280, w: 270, h: 200 },
  },
];

export function mapZoneIsHere(route: string, path: string, id: string): boolean {
  if (id === "lobby") {
    return path === "/casino/lobby" || path === "/casino/floor" || path === "/casino/map" || path.endsWith("/map");
  }
  if (path === route || path.startsWith(`${route}/`)) return true;
  if (id === "roulette" && path.includes("/roulette")) return true;
  if (id === "blackjack" && path.includes("blackjack")) return true;
  if (id === "slots" && (path.includes("/slots") || path.includes("odessa-gold"))) return true;
  if (id === "poker" && path.includes("poker")) return true;
  if (id === "vip" && path.includes("/vip")) return true;
  if (id === "bar" && (path.includes("/bar") || path.endsWith("/bar"))) return true;
  if (id === "restaurant" && path.includes("restaurant")) return true;
  return false;
}
