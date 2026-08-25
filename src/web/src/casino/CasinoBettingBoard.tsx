const RED = new Set([1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]);
const COLS = [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36];

export type BoardBet =
  | { key: string; bet_type: "straight"; numbers: number[] }
  | { key: string; bet_type: "red" | "black" | "even" | "odd" | "low" | "high" | "dozen_1" | "dozen_2" | "dozen_3" | "column_1" | "column_2" | "column_3" };

export function colorClass(n: number): string {
  if (n === 0) return "is-green";
  return RED.has(n) ? "is-red" : "is-black";
}

export function CasinoBettingBoard({
  stacks,
  onPick,
  win,
}: {
  stacks: Record<string, number>;
  onPick: (bet: BoardBet) => void;
  win?: number | null;
}) {
  return (
    <div className="op-board-scroll">
      <div className="op-board" role="group" aria-label="Поле европейской рулетки">
        <button type="button" className={`op-cell is-green${stacks["n:0"] ? " is-on" : ""}${win === 0 ? " is-win" : ""}`} style={{ gridRow: "1 / span 3" }} onClick={() => onPick({ key: "n:0", bet_type: "straight", numbers: [0] })}>
          0
          {stacks["n:0"] ? <span className="op-stack">{stacks["n:0"]}</span> : null}
        </button>
        {COLS.flatMap((top, col) => {
          const nums = [top - 2, top - 1, top];
          return nums.map((n, row) => (
            <button
              key={n}
              type="button"
              className={`op-cell ${colorClass(n)}${stacks[`n:${n}`] ? " is-on" : ""}${win === n ? " is-win" : ""}`}
              style={{ gridColumn: col + 2, gridRow: 3 - row }}
              onClick={() => onPick({ key: `n:${n}`, bet_type: "straight", numbers: [n] })}
            >
              {n}
              {stacks[`n:${n}`] ? <span className="op-stack">{stacks[`n:${n}`]}</span> : null}
            </button>
          ));
        })}
        {(["column_1", "column_2", "column_3"] as const).map((type, idx) => (
          <button
            key={type}
            type="button"
            className={`op-cell is-out${stacks[type] ? " is-on" : ""}`}
            style={{ gridColumn: 14, gridRow: 3 - idx }}
            onClick={() => onPick({ key: type, bet_type: type })}
          >
            2:1
            {stacks[type] ? <span className="op-stack">{stacks[type]}</span> : null}
          </button>
        ))}
        {(
          [
            ["dozen_1", "1st 12"],
            ["dozen_2", "2nd 12"],
            ["dozen_3", "3rd 12"],
          ] as const
        ).map(([type, label], i) => (
          <button
            key={type}
            type="button"
            className={`op-cell is-out${stacks[type] ? " is-on" : ""}`}
            style={{ gridColumn: `${2 + i * 4} / span 4`, gridRow: 4 }}
            onClick={() => onPick({ key: type, bet_type: type })}
          >
            {label}
            {stacks[type] ? <span className="op-stack">{stacks[type]}</span> : null}
          </button>
        ))}
        {(
          [
            ["low", "1–18"],
            ["even", "EVEN"],
            ["red", "RED"],
            ["black", "BLACK"],
            ["odd", "ODD"],
            ["high", "19–36"],
          ] as const
        ).map(([type, label], i) => (
          <button
            key={type}
            type="button"
            className={`op-cell is-out${stacks[type] ? " is-on" : ""}`}
            style={{ gridColumn: `${2 + i * 2} / span 2`, gridRow: 5 }}
            onClick={() => onPick({ key: type, bet_type: type })}
          >
            {label}
            {stacks[type] ? <span className="op-stack">{stacks[type]}</span> : null}
          </button>
        ))}
      </div>
    </div>
  );
}
