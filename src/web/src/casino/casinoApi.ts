import { apiFetch } from "@/integrations/apiClient";
import { webConfig } from "@/config/webConfig";
import type {
  BlackjackHand,
  CasinoLobby,
  CasinoLedgerEntry,
  CasinoRooms,
  CasinoTablePresence,
  CasinoVenue,
  CasinoWallet,
  RouletteRound,
  SlotSpin,
} from "./types";

const PREFIX = webConfig.casinoPrefix;

function throwIfAuthRequired(res: Response): void {
  if (res.status === 401) {
    const err = new Error("auth_required");
    err.name = "CasinoAuthError";
    throw err;
  }
}

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
  throwIfAuthRequired(res);
  return readJson<CasinoWallet>(res, "casino_wallet");
}

export async function fetchCasinoLedger(): Promise<{ items: CasinoLedgerEntry[] }> {
  const res = await apiFetch(`${PREFIX}/ledger`);
  throwIfAuthRequired(res);
  return readJson(res, "casino_ledger");
}

export async function grantDemoChips(): Promise<CasinoWallet> {
  const res = await apiFetch(`${PREFIX}/wallet/demo-grant`, {
    method: "POST",
    body: "{}",
  });
  throwIfAuthRequired(res);
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
  throwIfAuthRequired(res);
  return readJson<CasinoTablePresence>(res, "casino_join");
}

export async function leaveCasinoRoom(venueId: string, roomId?: string): Promise<CasinoTablePresence> {
  const path = roomId
    ? `${PREFIX}/venues/${encodeURIComponent(venueId)}/rooms/${encodeURIComponent(roomId)}/leave`
    : `${PREFIX}/venues/${encodeURIComponent(venueId)}/rooms/leave`;
  const res = await apiFetch(path, { method: "POST", body: "{}" });
  throwIfAuthRequired(res);
  return readJson<CasinoTablePresence>(res, "casino_leave");
}

export async function openRouletteRound(venueId: string): Promise<RouletteRound> {
  const res = await apiFetch(`${PREFIX}/venues/${encodeURIComponent(venueId)}/roulette/rounds`, {
    method: "POST",
    body: "{}",
  });
  throwIfAuthRequired(res);
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
  throwIfAuthRequired(res);
  return readJson(res, "casino_bet");
}

export async function spinRoulette(roundId: string): Promise<RouletteRound> {
  const res = await apiFetch(`${PREFIX}/roulette/rounds/${encodeURIComponent(roundId)}/spin`, {
    method: "POST",
    body: "{}",
  });
  throwIfAuthRequired(res);
  return readJson<RouletteRound>(res, "casino_spin");
}

export async function dealBlackjack(amountChips: number, idempotencyKey?: string): Promise<BlackjackHand> {
  const res = await apiFetch(`${PREFIX}/venues/odessa-prime/blackjack/hands`, {
    method: "POST",
    body: JSON.stringify({
      amount_chips: amountChips,
      idempotency_key: idempotencyKey || `bj:${Date.now()}`,
    }),
  });
  throwIfAuthRequired(res);
  return readJson<BlackjackHand>(res, "casino_bj_deal");
}

export async function hitBlackjack(handId: string): Promise<BlackjackHand> {
  const res = await apiFetch(`${PREFIX}/blackjack/hands/${encodeURIComponent(handId)}/hit`, {
    method: "POST",
    body: "{}",
  });
  throwIfAuthRequired(res);
  return readJson<BlackjackHand>(res, "casino_bj_hit");
}

export async function standBlackjack(handId: string): Promise<BlackjackHand> {
  const res = await apiFetch(`${PREFIX}/blackjack/hands/${encodeURIComponent(handId)}/stand`, {
    method: "POST",
    body: "{}",
  });
  throwIfAuthRequired(res);
  return readJson<BlackjackHand>(res, "casino_bj_stand");
}

export async function doubleBlackjack(handId: string): Promise<BlackjackHand> {
  const res = await apiFetch(`${PREFIX}/blackjack/hands/${encodeURIComponent(handId)}/double`, {
    method: "POST",
    body: "{}",
  });
  throwIfAuthRequired(res);
  return readJson<BlackjackHand>(res, "casino_bj_double");
}

export async function spinOdessaGold(amountChips: number, idempotencyKey?: string): Promise<SlotSpin> {
  const res = await apiFetch(`${PREFIX}/venues/odessa-prime/slots/odessa-gold/spin`, {
    method: "POST",
    body: JSON.stringify({
      amount_chips: amountChips,
      idempotency_key: idempotencyKey || `slot:${Date.now()}`,
    }),
  });
  throwIfAuthRequired(res);
  return readJson<SlotSpin>(res, "casino_slot");
}

export type { BlackjackHand, SlotSpin } from "./types";
export { CASINO_ROUTES } from "./state/casinoRoutes";
