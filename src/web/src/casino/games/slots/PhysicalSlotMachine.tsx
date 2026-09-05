import type { CSSProperties, MouseEvent } from "react";
import { Link } from "react-router-dom";
import { CASINO_ROUTES } from "../../state/casinoRoutes";
import { symbolLabel } from "./slotCatalog";
import type { SlotGameDefinition } from "./slotTypes";

type Props = {
  def: SlotGameDefinition;
  index: number;
  selected?: boolean;
  onSelect?: (id: string, href: string, event: MouseEvent<HTMLAnchorElement>) => void;
};

function reelGrid(def: SlotGameDefinition): string[][] {
  const cols = def.reelCount;
  const rows = def.rowCount;
  return Array.from({ length: cols }, (_, c) =>
    Array.from({ length: rows }, (_, r) => def.symbols[(c + r * 2) % def.symbols.length].id),
  );
}

export function PhysicalSlotMachine({ def, index, selected, onSelect }: Props) {
  const href = CASINO_ROUTES.slot(def.slug);
  const grid = reelGrid(def);
  return (
    <article
      className={`op-phys-cab variant-${def.cabinetVariant} theme-${def.theme} pos-${index}${selected ? " is-selected" : ""}`}
      data-testid={`slot-cabinet-${def.id}`}
      data-variant={def.cabinetVariant}
      style={{ "--cab-accent": def.accent, "--cab-accent-2": def.accent2 } as CSSProperties}
    >
      <div className="op-phys-reflect" aria-hidden />
      <Link
        className="op-phys-hit"
        to={href}
        data-testid={`slot-play-${def.id}`}
        onClick={(event) => onSelect?.(def.id, href, event)}
      >
        <div className="op-phys-shell">
          <div className="op-phys-led-rail is-top" aria-hidden />
          <header className="op-phys-topper">
            <p className="op-phys-marquee">{def.title}</p>
            <p className="op-phys-jackpot">
              JACKPOT <span>{def.jackpot}</span>
            </p>
          </header>
          <div className="op-phys-body">
            <span className="op-phys-led-side is-left" aria-hidden />
            <div className="op-phys-screen" data-testid={`slot-preview-${def.id}`}>
              <div className="op-phys-art" aria-hidden />
              <div className="op-phys-reels" aria-hidden>
                {grid.map((col, c) => (
                  <div key={c} className="op-phys-reel">
                    {col.map((sym, r) => (
                      <span key={`${c}-${r}`} className={r === 1 ? "is-hot" : undefined}>
                        {symbolLabel(def, sym)}
                      </span>
                    ))}
                  </div>
                ))}
              </div>
              <div className="op-phys-glass" aria-hidden />
              <div className="op-phys-sweep" aria-hidden />
            </div>
            <span className="op-phys-led-side is-right" aria-hidden />
          </div>
          <div className="op-phys-belly" aria-hidden>
            <strong>{def.title}</strong>
          </div>
          <div className="op-phys-panel" aria-hidden>
            <span>BET −</span>
            <span>BET +</span>
            <span className="op-phys-spin">SPIN</span>
            <span>MAX</span>
            <span>INFO</span>
          </div>
          <div className="op-phys-base" aria-hidden />
          <span className="op-phys-play">ИГРАТЬ</span>
        </div>
      </Link>
      <div className="op-phys-stool" aria-hidden />
    </article>
  );
}

export { PhysicalSlotMachine as SlotMachineCabinet };
