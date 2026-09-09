import { cabinetScreenRect } from "./cabinetAssets";
import type { OverlayRect } from "./cabinetPlayGeometry";
import type { SlotGameDefinition } from "./slotTypes";

export const PHYSICAL_BET_STEPS = [10, 25, 50, 100, 250, 500] as const;
export const INSERT_BILL_CREDITS = 500;

export type ControlShape = "rect" | "round" | "slot";
export type ControlAction =
  | "spin"
  | "bet"
  | "auto"
  | "cashout"
  | "service"
  | "insert-card"
  | "insert-bill"
  | "bet-step";

export type PhysicalControl = OverlayRect & {
  id: string;
  action: ControlAction;
  bet?: number;
  step?: -1 | 1;
  shape: ControlShape;
  ariaLabel: string;
  painted: boolean;
  note?: string;
};

type DeckBand = {
  left: number;
  top: number;
  width: number;
  height: number;
  gap: number;
};

type CabinetControlMap = {
  row: DeckBand;
  spin: OverlayRect;
  card: OverlayRect;
  bill: OverlayRect;
  auto: OverlayRect;
  extraBetTop: number;
};

/**
 * Percentage hit zones measured against each cabinet PNG.
 * Painted 6-across deck: CASH OUT, SERVICE, BET 50/100/250/500, circular SPIN,
 * INSERT CARD / INSERT BILL slots. BET 10/25 and AUTO are not drawn on the
 * source art — they use the nearest deck plate (documented on each control).
 */
const CABINET_CONTROL_MAP: Record<string, CabinetControlMap> = {
  "olympus-crown": {
    row: { left: 10.4, top: 73.95, width: 59.8, height: 4.85, gap: 1.2 },
    spin: { leftPct: 73.0, topPct: 72.15, widthPct: 12.2, heightPct: 7.8, borderRadius: 999 },
    card: { leftPct: 16.6, topPct: 65.2, widthPct: 13.6, heightPct: 3.7, borderRadius: 4 },
    bill: { leftPct: 59.6, topPct: 65.2, widthPct: 13.6, heightPct: 3.7, borderRadius: 4 },
    auto: { leftPct: 67.0, topPct: 73.9, widthPct: 5.2, heightPct: 5.0, borderRadius: 8 },
    extraBetTop: 68.7,
  },
  "lady-emerald": {
    row: { left: 20.4, top: 77.15, width: 47.6, height: 5.05, gap: 0.95 },
    spin: { leftPct: 69.8, topPct: 75.4, widthPct: 12.4, heightPct: 8.2, borderRadius: 999 },
    card: { leftPct: 22.2, topPct: 69.4, widthPct: 12.6, heightPct: 3.8, borderRadius: 4 },
    bill: { leftPct: 54.8, topPct: 69.4, widthPct: 12.6, heightPct: 3.8, borderRadius: 4 },
    auto: { leftPct: 64.4, topPct: 77.0, widthPct: 5.0, heightPct: 5.2, borderRadius: 8 },
    extraBetTop: 72.2,
  },
  "pharaohs-book": {
    row: { left: 18.6, top: 78.6, width: 51.2, height: 4.9, gap: 1.0 },
    spin: { leftPct: 71.4, topPct: 76.6, widthPct: 13.0, heightPct: 8.0, borderRadius: 999 },
    card: { leftPct: 20.4, topPct: 71.2, widthPct: 13.2, heightPct: 3.7, borderRadius: 4 },
    bill: { leftPct: 55.8, topPct: 71.2, widthPct: 13.2, heightPct: 3.7, borderRadius: 4 },
    auto: { leftPct: 66.2, topPct: 78.5, widthPct: 5.0, heightPct: 5.1, borderRadius: 8 },
    extraBetTop: 73.8,
  },
  "buffalo-fortune": {
    row: { left: 18.2, top: 78.85, width: 51.8, height: 4.95, gap: 1.0 },
    spin: { leftPct: 71.6, topPct: 76.8, widthPct: 13.2, heightPct: 8.1, borderRadius: 999 },
    card: { leftPct: 20.0, topPct: 71.4, widthPct: 13.4, heightPct: 3.7, borderRadius: 4 },
    bill: { leftPct: 56.0, topPct: 71.4, widthPct: 13.4, heightPct: 3.7, borderRadius: 4 },
    auto: { leftPct: 66.4, topPct: 78.7, widthPct: 5.0, heightPct: 5.1, borderRadius: 8 },
    extraBetTop: 74.0,
  },
  "candy-fortune": {
    row: { left: 21.6, top: 71.55, width: 46.8, height: 5.7, gap: 0.9 },
    spin: { leftPct: 69.6, topPct: 69.4, widthPct: 15.2, heightPct: 9.4, borderRadius: 999 },
    card: { leftPct: 22.8, topPct: 64.4, widthPct: 13.8, heightPct: 4.0, borderRadius: 4 },
    bill: { leftPct: 53.6, topPct: 64.4, widthPct: 13.8, heightPct: 4.0, borderRadius: 4 },
    auto: { leftPct: 64.6, topPct: 71.4, widthPct: 5.0, heightPct: 5.6, borderRadius: 8 },
    extraBetTop: 66.5,
  },
  "big-catch": {
    row: { left: 16.8, top: 76.2, width: 50.6, height: 5.2, gap: 0.95 },
    spin: { leftPct: 69.8, topPct: 74.0, widthPct: 16.0, heightPct: 9.2, borderRadius: 999 },
    card: { leftPct: 18.6, topPct: 68.8, widthPct: 14.0, heightPct: 3.9, borderRadius: 4 },
    bill: { leftPct: 52.8, topPct: 68.8, widthPct: 14.0, heightPct: 3.9, borderRadius: 4 },
    auto: { leftPct: 64.2, topPct: 76.0, widthPct: 5.2, heightPct: 5.4, borderRadius: 8 },
    extraBetTop: 71.2,
  },
};

const ROW_ACTIONS = [
  { action: "cashout" as const, id: "cashout", ariaLabel: "Вывести демо-баланс", painted: true },
  { action: "service" as const, id: "service", ariaLabel: "Сервис", painted: true },
  { action: "bet" as const, id: "bet-50", bet: 50, ariaLabel: "Ставка 50", painted: true },
  { action: "bet" as const, id: "bet-100", bet: 100, ariaLabel: "Ставка 100", painted: true },
  { action: "bet" as const, id: "bet-250", bet: 250, ariaLabel: "Ставка 250", painted: true },
  { action: "bet" as const, id: "bet-500", bet: 500, ariaLabel: "Ставка 500", painted: true },
];

function splitRow(band: DeckBand): OverlayRect[] {
  const inner = band.width - band.gap * (ROW_ACTIONS.length - 1);
  const width = inner / ROW_ACTIONS.length;
  return ROW_ACTIONS.map((_, index) => ({
    leftPct: band.left + index * (width + band.gap),
    topPct: band.top,
    widthPct: width,
    heightPct: band.height,
    borderRadius: 6,
  }));
}

function rect(base: OverlayRect, extra: Omit<PhysicalControl, keyof OverlayRect>): PhysicalControl {
  return { ...base, ...extra };
}

export function cabinetControls(def: Pick<SlotGameDefinition, "id" | "cabinetVariant">): PhysicalControl[] {
  const map = CABINET_CONTROL_MAP[def.id] ?? CABINET_CONTROL_MAP["olympus-crown"];
  const cells = splitRow(map.row);
  const painted = ROW_ACTIONS.map((item, index) =>
    rect(cells[index]!, {
      id: item.id,
      action: item.action,
      bet: item.bet,
      shape: "rect",
      ariaLabel: item.ariaLabel,
      painted: true,
    }),
  );
  const bet50 = cells[2]!;
  const bet100 = cells[3]!;
  const extras: PhysicalControl[] = [
    rect(
      { ...bet50, topPct: map.extraBetTop, heightPct: Math.max(3.4, bet50.heightPct * 0.72) },
      {
        id: "bet-10",
        action: "bet",
        bet: 10,
        shape: "rect",
        ariaLabel: "Ставка 10",
        painted: false,
        note: "PNG paints four credit keys (50–500). BET 10 uses the deck plate directly above BET 50.",
      },
    ),
    rect(
      { ...bet100, topPct: map.extraBetTop, heightPct: Math.max(3.4, bet100.heightPct * 0.72) },
      {
        id: "bet-25",
        action: "bet",
        bet: 25,
        shape: "rect",
        ariaLabel: "Ставка 25",
        painted: false,
        note: "PNG paints four credit keys (50–500). BET 25 uses the deck plate directly above BET 100.",
      },
    ),
    rect(map.spin, {
      id: "spin",
      action: "spin",
      shape: "round",
      ariaLabel: "Крутить барабаны",
      painted: true,
    }),
    rect(map.auto, {
      id: "auto",
      action: "auto",
      shape: "rect",
      ariaLabel: "Автоигра",
      painted: false,
      note: "No AUTO key is painted. Hit zone sits on the deck plate immediately left of SPIN.",
    }),
    rect(map.card, {
      id: "insert-card",
      action: "insert-card",
      shape: "slot",
      ariaLabel: "Вставить карту",
      painted: true,
    }),
    rect(map.bill, {
      id: "insert-bill",
      action: "insert-bill",
      shape: "slot",
      ariaLabel: "Вставить купюру",
      painted: true,
    }),
    rect(
      { leftPct: map.row.left - 0.2, topPct: map.row.top, widthPct: 2.2, heightPct: map.row.height, borderRadius: 6 },
      {
        id: "bet-minus",
        action: "bet-step",
        step: -1,
        shape: "rect",
        ariaLabel: "Уменьшить ставку",
        painted: false,
        note: "Stepper uses the left edge of the painted deck row.",
      },
    ),
    rect(
      {
        leftPct: map.row.left + map.row.width - 0.4,
        topPct: map.row.top,
        widthPct: 2.2,
        heightPct: map.row.height,
        borderRadius: 6,
      },
      {
        id: "bet-plus",
        action: "bet-step",
        step: 1,
        shape: "rect",
        ariaLabel: "Увеличить ставку",
        painted: false,
        note: "Stepper uses the right edge of the painted deck row.",
      },
    ),
  ];
  return [...painted, ...extras];
}

export function controlTestId(control: PhysicalControl): string {
  if (control.action === "bet" && control.bet != null) return `slot-bet-${control.bet}`;
  if (control.action === "bet-step") return control.step === 1 ? "slot-bet-plus" : "slot-bet-minus";
  if (control.action === "spin") return "slot-spin";
  if (control.action === "auto") return "slot-auto";
  if (control.action === "cashout") return "slot-cashout";
  if (control.action === "service") return "slot-service";
  if (control.action === "insert-card") return "slot-insert-card";
  return "slot-insert-bill";
}

export function boundsOf(controls: PhysicalControl[]): OverlayRect {
  const left = Math.min(...controls.map((item) => item.leftPct));
  const top = Math.min(...controls.map((item) => item.topPct));
  const right = Math.max(...controls.map((item) => item.leftPct + item.widthPct));
  const bottom = Math.max(...controls.map((item) => item.topPct + item.heightPct));
  return { leftPct: left, topPct: top, widthPct: right - left, heightPct: bottom - top };
}

export function screenMetersRect(def: Pick<SlotGameDefinition, "id" | "cabinetVariant">, screen: OverlayRect): OverlayRect {
  void cabinetScreenRect(def);
  return {
    leftPct: screen.leftPct + 2.2,
    topPct: screen.topPct + screen.heightPct - 8.2,
    widthPct: screen.widthPct - 4.4,
    heightPct: 7.4,
    borderRadius: 6,
  };
}
