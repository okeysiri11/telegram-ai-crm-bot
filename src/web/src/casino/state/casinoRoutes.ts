export const CASINO_ROUTES = {
  lobby: "/casino",
  floor: "/casino/floor",
  lobbyAlias: "/casino/lobby",
  map: "/casino/map",
  games: "/casino/games",
  tables: "/casino/roulette",
  rouletteHall: "/casino/rooms/roulette",
  rouletteLive: "/casino/roulette/royale-1",
  blackjackRoom: "/casino/rooms/blackjack",
  slotsRoom: "/casino/rooms/slots",
  pokerRoom: "/casino/rooms/poker",
  vipRoom: "/casino/rooms/vip",
  restaurantRoom: "/casino/rooms/restaurant",
  barRoom: "/casino/rooms/bar",
  venue: (id: string) => `/casino/venues/${id}`,
  roulette: (id: string) => `/casino/venues/${id}/roulette`,
  table: (tableId: string) => {
    const id = resolveRouletteTableId(tableId);
    if (id === "roulette-royale-1") return "/casino/roulette/royale-1";
    return `/casino/roulette/${id}`;
  },
  slot: (machineId: string) => `/casino/slots/${machineId}`,
  cityReturn: "/enterprise-city?building=casino",
} as const;

const TABLE_ALIASES: Record<string, string> = {
  "royale-1": "roulette-royale-1",
  royale: "roulette-royale-1",
  table: "roulette-royale-1",
  "roulette-royale": "roulette-royale-1",
};

export function resolveRouletteTableId(raw?: string | null): string {
  const id = (raw || "").trim().toLowerCase();
  if (!id) return "roulette-royale-1";
  return TABLE_ALIASES[id] || id;
}

export function isLiveRouletteTable(raw?: string | null): boolean {
  return resolveRouletteTableId(raw) === "roulette-royale-1";
}

export type CasinoRoomId =
  | "lobby"
  | "roulette"
  | "blackjack"
  | "slots"
  | "poker"
  | "vip"
  | "restaurant"
  | "bar";

export const ROOM_CATALOG: Array<{
  id: CasinoRoomId;
  label: string;
  route: string;
  live: boolean;
  hotspot: string;
}> = [
  { id: "lobby", label: "ЛОББИ", route: "/casino/lobby", live: true, hotspot: "hall" },
  { id: "roulette", label: "РУЛЕТКА", route: "/casino/roulette/royale-1", live: true, hotspot: "roulette" },
  { id: "blackjack", label: "BLACKJACK", route: "/casino/blackjack", live: true, hotspot: "blackjack" },
  { id: "slots", label: "АВТОМАТЫ", route: "/casino/slots", live: true, hotspot: "slots" },
  { id: "poker", label: "ПОКЕР", route: "/casino/poker", live: true, hotspot: "poker" },
  { id: "vip", label: "VIP", route: "/casino/vip", live: true, hotspot: "vip" },
  { id: "restaurant", label: "РЕСТОРАН", route: "/casino/restaurant", live: true, hotspot: "restaurant" },
  { id: "bar", label: "БАР", route: "/casino/bar", live: true, hotspot: "bar" },
];

export const ROOM_CYCLE: CasinoRoomId[] = ["roulette", "blackjack", "slots", "poker", "vip", "bar", "restaurant"];
