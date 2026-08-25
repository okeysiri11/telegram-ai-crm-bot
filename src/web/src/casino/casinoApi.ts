import { apiFetch } from "@/integrations/apiClient";
import { webConfig } from "@/config/webConfig";
import type {
  CasinoLobby,
  CasinoLedgerEntry,
  CasinoRooms,
  CasinoTablePresence,
  CasinoVenue,
  CasinoWallet,
  RouletteRound,
} from "./types";

const PREFIX = webConfig.casinoPrefix;

async function readJson<T>(res: Response, label: string): Promise<T> {
  if (!res.ok) {
    let detail = `${label}_${res.status}`;
    try {
      const body = (await res.json()) as { error?: string; retry_after_seconds?: number };
      if (body.error) detail = body.error;
      if (body.retry_after_seconds) detail = `${detail}:${body.retry_after_seconds}`;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

export async function fetchCasinoLobby(): Promise<CasinoLobby> {
  const res = await apiFetch(`${PREFIX}/lobby`, { anonymous: true });
  return readJson<CasinoLobby>(res, "casino_lobby");
}

export async function fetchCasinoVenue(venueId: string): Promise<CasinoVenue> {
  const res = await apiFetch(`${PREFIX}/venues/${encodeURIComponent(venueId)}`, { anonymous: true });
  return readJson<CasinoVenue>(res, "casino_venue");
}

export async function fetchCasinoHealth(): Promise<{ status: string; play_money_only: boolean }> {
  const res = await apiFetch(`${PREFIX}/health`, { anonymous: true });
  return readJson(res, "casino_health");
}

export async function fetchCasinoWallet(): Promise<CasinoWallet> {
  const res = await apiFetch(`${PREFIX}/wallet`);
  if (res.status === 401) {
    const err = new Error("auth_required");
    err.name = "CasinoAuthError";
    throw err;
  }
  return readJson<CasinoWallet>(res, "casino_wallet");
}

export async function fetchCasinoLedger(): Promise<{ items: CasinoLedgerEntry[] }> {
  const res = await apiFetch(`${PREFIX}/ledger`);
  if (res.status === 401) {
    const err = new Error("auth_required");
    err.name = "CasinoAuthError";
    throw err;
  }
  return readJson(res, "casino_ledger");
}

export async function grantDemoChips(): Promise<CasinoWallet> {
  const res = await apiFetch(`${PREFIX}/wallet/demo-grant`, {
    method: "POST",
    body: "{}",
  });
  return readJson<CasinoWallet>(res, "casino_demo_grant");
}

export async function fetchCasinoRooms(venueId: string): Promise<CasinoRooms> {
  const res = await apiFetch(`${PREFIX}/venues/${encodeURIComponent(venueId)}/rooms`, { anonymous: true });
  return readJson<CasinoRooms>(res, "casino_rooms");
}

export async function joinCasinoRoom(venueId: string, roomId?: string): Promise<CasinoTablePresence> {
  const path = roomId
    ? `${PREFIX}/venues/${encodeURIComponent(venueId)}/rooms/${encodeURIComponent(roomId)}/join`
    : `${PREFIX}/venues/${encodeURIComponent(venueId)}/rooms/join`;
  const res = await apiFetch(path, { method: "POST", body: "{}" });
  return readJson<CasinoTablePresence>(res, "casino_join");
}

export async function leaveCasinoRoom(venueId: string, roomId?: string): Promise<CasinoTablePresence> {
  const path = roomId
    ? `${PREFIX}/venues/${encodeURIComponent(venueId)}/rooms/${encodeURIComponent(roomId)}/leave`
    : `${PREFIX}/venues/${encodeURIComponent(venueId)}/rooms/leave`;
  const res = await apiFetch(path, { method: "POST", body: "{}" });
  return readJson<CasinoTablePresence>(res, "casino_leave");
}

export async function openRouletteRound(venueId: string): Promise<RouletteRound> {
  const res = await apiFetch(`${PREFIX}/venues/${encodeURIComponent(venueId)}/roulette/rounds`, {
    method: "POST",
    body: "{}",
  });
  return readJson<RouletteRound>(res, "casino_round");
}

export async function placeRouletteBet(
  roundId: string,
  body: { bet_type: string; amount_chips: number; numbers?: number[]; idempotency_key: string },
): Promise<unknown> {
  const res = await apiFetch(`${PREFIX}/roulette/rounds/${encodeURIComponent(roundId)}/bets`, {
    method: "POST",
    body: JSON.stringify(body),
  });
  return readJson(res, "casino_bet");
}

export async function spinRoulette(roundId: string): Promise<RouletteRound> {
  const res = await apiFetch(`${PREFIX}/roulette/rounds/${encodeURIComponent(roundId)}/spin`, {
    method: "POST",
    body: "{}",
  });
  return readJson<RouletteRound>(res, "casino_spin");
}

export const CASINO_ROUTES = {
  lobby: "/casino",
  floor: "/casino/floor",
  games: "/casino/games",
  tables: "/casino/roulette",
  venue: (id: string) => `/casino/venues/${id}`,
  roulette: (id: string) => `/casino/venues/${id}/roulette`,
  table: (tableId: string) => `/casino/roulette/${tableId}`,
} as const;
