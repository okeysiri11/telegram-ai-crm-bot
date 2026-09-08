import { symbolLabel } from "./slotCatalog";
import type { SlotGameDefinition } from "./slotTypes";

function idleGrid(def: SlotGameDefinition): string[][] {
  return Array.from({ length: def.reelCount }, (_, c) =>
    Array.from({ length: def.rowCount }, (_, r) => def.symbols[(c + r * 2) % def.symbols.length].id),
  );
}

export function SlotReels({
  def,
  grid,
  spinning,
}: {
  def?: SlotGameDefinition;
  grid: string[][];
  spinning: boolean;
}) {
  const cols = grid.length ? grid : def ? idleGrid(def) : [];
  return (
    <div className={`op-cab-reels${spinning ? " is-spinning" : ""}`} data-testid="slot-reels">
      {cols.map((col, c) => {
        const strip = def
          ? [...def.symbols.map((s) => s.id), ...col, ...def.symbols.map((s) => s.id)]
          : [...col, ...col];
        return (
          <div key={c} className="op-cab-reel" style={{ animationDelay: `${c * 80}ms` }}>
            <div
              className={`op-cab-reel-strip${spinning ? " is-spinning" : ""}`}
              style={{ animationDelay: `${c * 80}ms` }}
            >
              {spinning
                ? strip.map((sym, r) => (
                    <span key={`${c}-${r}`}>{def ? symbolLabel(def, sym) : sym}</span>
                  ))
                : col.map((sym, r) => (
                    <span key={`${c}-${r}`} className={r === 1 ? "is-pay" : undefined}>
                      {def ? symbolLabel(def, sym) : sym}
                    </span>
                  ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
