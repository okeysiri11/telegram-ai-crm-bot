import { symbolLabel } from "./slotCatalog";
import type { SlotGameDefinition } from "./slotTypes";

export function SlotReels({
  def,
  grid,
  spinning,
}: {
  def?: SlotGameDefinition;
  grid: string[][];
  spinning: boolean;
}) {
  const cols = grid.length ? grid : Array.from({ length: def?.reelCount || 5 }, () =>
    Array.from({ length: def?.rowCount || 3 }, () => def?.symbols[0]?.id || "CHERRY"),
  );
  return (
    <div className={`op-reels${spinning ? " is-spinning" : ""}`} data-testid="slot-reels">
      {cols.map((col, c) => (
        <div key={c} className="op-reel" style={{ animationDelay: `${c * 90}ms` }}>
          {col.map((sym, r) => (
            <span key={`${c}-${r}`}>{def ? symbolLabel(def, sym) : sym}</span>
          ))}
        </div>
      ))}
    </div>
  );
}
