export type CasinoVenue = {
  venue_id: string;
  slug: string;
  name: string;
  city_building_id: string;
  city_route: string;
  game: string;
  status: string;
  play_money_only: boolean;
  real_money: boolean;
};

export type CasinoFloorArea = {
  id: string;
  label: string;
  label_ru: string;
  status: string;
  status_label: string;
  coming_soon: boolean;
  game?: string;
  room_id?: string;
  route?: string;
};

export type CasinoLobby = {
  title: string;
  play_money_only: boolean;
  real_money_implemented: boolean;
  currency_label?: string;
  display_currency?: string;
  chip_denoms?: number[];
  venues: CasinoVenue[];
  games: { id: string; name: string; demo: boolean }[];
  floor?: CasinoFloorArea[];
  city_entry: { building_id: string; route: string; venue_route: string; enter_label?: string };
};

export type CasinoWallet = {
  wallet_id: string;
  tenant_id: string;
  balance_chips: number;
  currency_code: string;
  currency_label: string;
  display_currency: string;
  play_money_only: boolean;
  real_money: boolean;
  demo_grant_chips?: number;
  demo_grant_available?: boolean;
  demo_grant_retry_after_seconds?: number;
  demo_grant_capped?: boolean;
};

export type CasinoLedgerEntry = {
  entry_id: string;
  created_ts: number;
  entry_type: string;
  operation: string;
  wager: number | null;
  win_loss: "win" | "loss" | null;
  balance_delta: number;
  resulting_balance: number;
  amount_chips: number;
  balance_after: number;
  reference_type?: string;
  currency_label?: string;
  display_currency?: string;
};

export type CasinoSeat = {
  seat: number;
  occupied: boolean;
  display_name: string | null;
};

export type CasinoTablePresence = {
  venue_id: string;
  room_id: string;
  table: string;
  game: string | null;
  count: number;
  seats_total: number;
  seats_taken: number;
  online_count: number;
  status: string;
  status_label: string;
  coming_soon: boolean;
  reconnected?: boolean;
  players: CasinoSeat[];
  seats: CasinoSeat[];
  route?: string | null;
};

export type CasinoRooms = {
  venue_id: string;
  tables: CasinoTablePresence[];
  count: number;
  online_count: number;
  play_money_only: boolean;
};

export type BlackjackHand = {
  hand_id: string;
  status: string;
  settled: boolean;
  wager_chips: number;
  player_cards: Array<{ rank: string; suit: string; hidden?: boolean }>;
  dealer_cards: Array<{ rank: string; suit: string; hidden?: boolean }>;
  player_total: number;
  dealer_total: number | null;
  available_actions: string[];
  settlement?: { outcome: string; payout_chips: number; server_authoritative: boolean };
  server_authoritative: boolean;
};

export type SlotSpin = {
  spin_id: string;
  machine: string;
  wager_chips: number;
  reels: string[][];
  payout_chips: number;
  outcome: string;
  server_authoritative: boolean;
};

export type RouletteRound = {
  round_id: string;
  status: string;
  result_number: number | null;
  result_color: string | null;
  settled: boolean;
  server_authoritative: boolean;
  duplicate_settlement_guard?: boolean;
  bets?: Array<{
    bet_id: string;
    bet_type: string;
    amount_chips: number;
    status: string;
    payout_chips: number;
  }>;
};
