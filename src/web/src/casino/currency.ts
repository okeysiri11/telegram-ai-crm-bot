/** Play-money labels only. Never render withdrawable-currency symbols. */

export const PLAY_LABEL = "PLAY";
export const DEMO_CHIPS_LABEL = "DEMO CHIPS";
export const CHIP_DENOMS = [1, 5, 10, 25, 50, 100, 500] as const;

const MONEY_SYMBOL = /[$€£¥₽₴]/;

export function formatPlayBalance(chips: number, label: string = PLAY_LABEL): string {
  const safe = Number.isFinite(chips) ? Math.trunc(chips) : 0;
  return `${safe.toLocaleString("ru-RU")} ${label}`;
}

export function formatDemoChips(chips: number): string {
  return `${formatPlayBalance(chips, PLAY_LABEL)} · ${DEMO_CHIPS_LABEL}`;
}

export function assertPlayMoneyCopy(text: string): boolean {
  return !MONEY_SYMBOL.test(text);
}

export function formatLedgerDelta(delta: number): string {
  const sign = delta > 0 ? "+" : "";
  return `${sign}${delta.toLocaleString("ru-RU")} ${PLAY_LABEL}`;
}

export function formatTimestamp(ts: number): string {
  if (!ts) return "—";
  const date = new Date(ts * 1000);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("ru-RU", { hour12: false });
}
