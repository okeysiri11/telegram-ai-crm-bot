import type { SlotGameDefinition, SlotSpinResult } from "./slotTypes";

export type SlotRng = () => number;

export function createSlotRng(seed?: number): SlotRng {
  if (seed == null) return () => Math.random();
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(1664525, state) + 1013904223) >>> 0;
    return state / 0x100000000;
  };
}

function pickSymbol(def: SlotGameDefinition, rng: SlotRng): string {
  const total = def.symbols.reduce((sum, item) => sum + item.weight, 0);
  let roll = rng() * total;
  for (const item of def.symbols) {
    roll -= item.weight;
    if (roll <= 0) return item.id;
  }
  return def.symbols[def.symbols.length - 1].id;
}

export function generateSlotGrid(def: SlotGameDefinition, rng: SlotRng): string[][] {
  return Array.from({ length: def.reelCount }, () =>
    Array.from({ length: def.rowCount }, () => pickSymbol(def, rng)),
  );
}

export function evaluateSlotGrid(def: SlotGameDefinition, grid: string[][], bet: number): number {
  let win = 0;
  for (let row = 0; row < def.rowCount; row += 1) {
    const first = grid[0]?.[row];
    if (!first) continue;
    let run = 1;
    for (let col = 1; col < def.reelCount; col += 1) {
      if (grid[col]?.[row] === first) run += 1;
      else break;
    }
    if (run < 3) continue;
    const payout = def.symbols.find((item) => item.id === first)?.payout || 1;
    const lineMult = run >= 5 ? 20 : run === 4 ? 8 : 3;
    win += Math.floor((bet * payout * lineMult) / 10);
  }
  return win;
}

export function clampSlotBet(def: SlotGameDefinition, bet: number): number {
  if (def.betSteps.includes(bet)) return bet;
  return def.betSteps[0] ?? def.minBet;
}

export function resolveSlotSpin(
  def: SlotGameDefinition,
  bet: number,
  rng: SlotRng = createSlotRng(),
): SlotSpinResult {
  const wager = clampSlotBet(def, bet);
  const grid = generateSlotGrid(def, rng);
  const win = evaluateSlotGrid(def, grid, wager);
  return {
    spinId: `demo-${def.id}-${Date.now()}-${Math.floor(rng() * 1e9)}`,
    machineId: def.id,
    title: def.title,
    bet: wager,
    grid,
    win,
    outcome: win > 0 ? "win" : "loss",
    ts: Date.now(),
  };
}
