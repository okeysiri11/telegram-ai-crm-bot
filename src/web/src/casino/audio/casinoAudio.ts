import { casinoSound, type CasinoRoomTone } from "../casinoSound";

export type { CasinoRoomTone };

export function roomToneFromPath(pathname: string): CasinoRoomTone {
  if (pathname === "/casino" || pathname === "/casino/") return "entrance";
  if (pathname.includes("/rooms/roulette") || pathname.includes("/roulette")) return "roulette";
  if (pathname.includes("blackjack")) return "blackjack";
  if (pathname.includes("slots") || pathname.includes("odessa-gold")) return "slots";
  if (pathname.includes("poker")) return "poker";
  if (pathname.includes("vip")) return "vip";
  if (pathname.includes("restaurant")) return "restaurant";
  if (pathname.includes("/bar")) return "bar";
  if (pathname.includes("/floor") || pathname.includes("/map") || pathname.includes("/games") || pathname.includes("/lobby")) {
    return "lobby";
  }
  return "lobby";
}

/** Bind path → room tone. Never autoplays ambience. */
export function bindCasinoRoomAudio(pathname: string) {
  casinoSound.setRoom(roomToneFromPath(pathname));
}
