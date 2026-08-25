export const CASINO_ROUTES = {
  lobby: "/casino",
  floor: "/casino/floor",
  lobbyAlias: "/casino/lobby",
  map: "/casino/map",
  games: "/casino/games",
  tables: "/casino/roulette",
  rouletteHall: "/casino/rooms/roulette",
  blackjackRoom: "/casino/rooms/blackjack",
  slotsRoom: "/casino/rooms/slots",
  pokerRoom: "/casino/rooms/poker",
  vipRoom: "/casino/rooms/vip",
  restaurantRoom: "/casino/rooms/restaurant",
  barRoom: "/casino/rooms/bar",
  venue: (id: string) => `/casino/venues/${id}`,
  roulette: (id: string) => `/casino/venues/${id}/roulette`,
  table: (tableId: string) => `/casino/roulette/${tableId}`,
  slot: (machineId: string) => `/casino/slots/${machineId}`,
  cityReturn: "/enterprise-city?building=casino",
} as const;

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
  { id: "lobby", label: "ЛОББИ", route: "/casino/floor", live: true, hotspot: "hall" },
  { id: "roulette", label: "РУЛЕТКА", route: "/casino/rooms/roulette", live: true, hotspot: "roulette" },
  { id: "blackjack", label: "BLACKJACK", route: "/casino/rooms/blackjack", live: true, hotspot: "blackjack" },
  { id: "slots", label: "АВТОМАТЫ", route: "/casino/rooms/slots", live: true, hotspot: "slots" },
  { id: "poker", label: "ПОКЕР", route: "/casino/rooms/poker", live: true, hotspot: "poker" },
  { id: "vip", label: "VIP", route: "/casino/rooms/vip", live: true, hotspot: "vip" },
  { id: "restaurant", label: "РЕСТОРАН", route: "/casino/rooms/restaurant", live: true, hotspot: "restaurant" },
  { id: "bar", label: "БАР", route: "/casino/rooms/bar", live: true, hotspot: "bar" },
];
