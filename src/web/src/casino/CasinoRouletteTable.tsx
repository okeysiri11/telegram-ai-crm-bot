import { Button } from "@/ui";
import { CHIP_DENOMS } from "./currency";

const RED = new Set([1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]);
const COLS = [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36];

function colorClass(n: number): string {
  if (n === 0) return "is-green";
  return RED.has(n) ? "is-red" : "is-black";
}

export type RouletteSelection =
  | { bet_type: "red" | "black" | "even" | "odd"; numbers?: undefined }
  | { bet_type: "straight"; numbers: number[] };

export function CasinoRouletteTable({
  chip,
  selection,
  busy,
  lastNumber,
  lastColor,
  onChip,
  onSelect,
  onPlay,
}: {
  chip: number;
  selection: RouletteSelection | null;
  busy: boolean;
  lastNumber: number | null;
  lastColor: string | null;
  onChip: (value: number) => void;
  onSelect: (next: RouletteSelection) => void;
  onPlay: () => void;
}) {
  const selectedStraight = selection?.bet_type === "straight" ? selection.numbers[0] : null;
  return (
    <div>
      <div className="casino-chip-row" role="group" aria-label="Номинал фишки PLAY">
        {CHIP_DENOMS.map((value) => (
          <button
            key={value}
            type="button"
            className={`casino-chip${chip === value ? " is-active" : ""}`}
            aria-pressed={chip === value}
            aria-label={`${value} PLAY`}
            onClick={() => onChip(value)}
          >
            {value}
          </button>
        ))}
      </div>
      <div className="casino-table-scroll">
        <div className="casino-felt" role="group" aria-label="Игровое поле рулетки">
          <button
            type="button"
            className={`casino-num casino-zero is-green${selectedStraight === 0 ? " is-selected" : ""}`}
            onClick={() => onSelect({ bet_type: "straight", numbers: [0] })}
          >
            0
          </button>
          {COLS.flatMap((top, col) => {
            const nums = [top - 2, top - 1, top];
            return nums.map((n, row) => (
              <button
                key={n}
                type="button"
                className={`casino-num ${colorClass(n)}${selectedStraight === n ? " is-selected" : ""}`}
                style={{ gridColumn: col + 2, gridRow: 3 - row }}
                onClick={() => onSelect({ bet_type: "straight", numbers: [n] })}
              >
                {n}
              </button>
            ));
          })}
          {(
            [
              ["red", "RED"],
              ["black", "BLACK"],
              ["even", "EVEN"],
              ["odd", "ODD"],
            ] as const
          ).map(([type, label]) => (
            <button
              key={type}
              type="button"
              className={`casino-out${selection?.bet_type === type ? " is-selected" : ""}`}
              onClick={() => onSelect({ bet_type: type })}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      <div className="casino-actions" style={{ marginTop: "0.85rem" }}>
        {lastNumber != null ? (
          <span className={`casino-result is-${lastColor || "green"}`} aria-label="Результат сервера">
            {lastNumber}
          </span>
        ) : null}
        <Button loading={busy} onClick={onPlay} disabled={!selection}>
          Поставить {chip} PLAY
        </Button>
      </div>
    </div>
  );
}
