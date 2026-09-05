export type SlotFilterId = "all" | "new" | "popular" | "classic" | "jackpot";

export type SlotSymbolDef = {
  id: string;
  label: string;
  weight: number;
  payout: number;
};

export type SlotGameDefinition = {
  id: string;
  slug: string;
  title: string;
  subtitle: string;
  theme: string;
  accent: string;
  accent2: string;
  provider: string;
  providerId: string;
  externalGameId: string;
  launchUrl?: string;
  thumbnail?: string;
  availability: "demo";
  currencySupport: ["DEMO"];
  demoAvailable: true;
  realAvailable: false;
  tags: SlotFilterId[];
  symbols: SlotSymbolDef[];
  reelCount: number;
  rowCount: number;
  paylines: number;
  minBet: number;
  maxBet: number;
  betSteps: number[];
  demoStartingBalance: number;
  cabinetVariant: "curved" | "square" | "slim";
  jackpot: string;
};

export type SlotSpinResult = {
  spinId: string;
  machineId: string;
  title: string;
  bet: number;
  grid: string[][];
  win: number;
  outcome: "win" | "loss";
  ts: number;
};

export type SlotHistoryItem = {
  game: string;
  machineId: string;
  bet: number;
  win: number;
  ts: number;
};
