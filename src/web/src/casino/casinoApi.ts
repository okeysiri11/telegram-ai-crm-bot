import { apiFetch } from "@/integrations/apiClient";
import { webConfig } from "@/config/webConfig";
import type { CasinoLobby, CasinoVenue } from "./types";

const PREFIX = webConfig.casinoPrefix;

export async function fetchCasinoLobby(): Promise<CasinoLobby> {
  const res = await apiFetch(`${PREFIX}/lobby`, { anonymous: true });
  if (!res.ok) throw new Error(`casino_lobby_${res.status}`);
  return (await res.json()) as CasinoLobby;
}

export async function fetchCasinoVenue(venueId: string): Promise<CasinoVenue> {
  const res = await apiFetch(`${PREFIX}/venues/${encodeURIComponent(venueId)}`, { anonymous: true });
  if (!res.ok) throw new Error(`casino_venue_${res.status}`);
  return (await res.json()) as CasinoVenue;
}

export async function fetchCasinoHealth(): Promise<{ status: string; play_money_only: boolean }> {
  const res = await apiFetch(`${PREFIX}/health`, { anonymous: true });
  if (!res.ok) throw new Error(`casino_health_${res.status}`);
  return (await res.json()) as { status: string; play_money_only: boolean };
}

export const CASINO_ROUTES = {
  lobby: "/casino",
  venue: (id: string) => `/casino/venues/${id}`,
  roulette: (id: string) => `/casino/venues/${id}/roulette`,
} as const;
