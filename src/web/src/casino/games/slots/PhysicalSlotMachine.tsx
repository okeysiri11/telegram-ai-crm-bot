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
  return Array.from({ length: def.reelCount }, (_, c) =>
    Array.from({ length: def.rowCount }, (_, r) => def.symbols[(c + r * 2) % def.symbols.length].id),
  );
}

function ChairSilhouette() {
  return (
    <svg className="op-phys-chair-svg" viewBox="0 0 80 42" aria-hidden>
      <path d="M24 2h32c4 0 7 3 7 7v11H17V9c0-4 3-7 7-7z" fill="#1a1618" />
      <path d="M12 20h56l3 7H9z" fill="#141216" />
      <path d="M18 27h44v4H18z" fill="#0e0c0f" />
      <path d="M22 31h7v11h-7zM51 31h7v11h-7z" fill="#121014" />
      <ellipse cx="25.5" cy="41" rx="6" ry="1.4" fill="#09080a" />
      <ellipse cx="54.5" cy="41" rx="6" ry="1.4" fill="#09080a" />
    </svg>
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
          <div className="op-phys-side is-left" aria-hidden />
          <div className="op-phys-side is-right" aria-hidden />
          <div className="op-phys-crown" aria-hidden />
          <header className="op-phys-topper" data-testid={`slot-topper-${def.id}`}>
            <div className="op-phys-led-rail is-top" aria-hidden />
            <p className="op-phys-marquee">{def.title}</p>
            <p className="op-phys-jackpot">
              JACKPOT <span>{def.jackpot}</span>
            </p>
          </header>
          <div className="op-phys-hood">
            <span className="op-phys-led-side is-left" aria-hidden />
            <div className="op-phys-screen" data-testid={`slot-preview-${def.id}`}>
              <div className="op-phys-art" aria-hidden />
              <div className="op-phys-reels" data-testid={`slot-reels-${def.id}`}>
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
          <div className="op-phys-deck">
            <div className="op-phys-panel" data-testid={`slot-controls-${def.id}`} aria-hidden>
              <span>BET −</span>
              <span>BET +</span>
              <span className="op-phys-spin">SPIN</span>
              <span>MAX</span>
              <span>INFO</span>
            </div>
          </div>
          <div className="op-phys-base" aria-hidden>
            <span className="op-phys-tray" />
          </div>
          <span className="op-phys-play">ИГРАТЬ</span>
        </div>
      </Link>
      <div className="op-phys-stool" data-testid={`slot-chair-${def.id}`} aria-hidden>
        <ChairSilhouette />
      </div>
    </article>
  );
}

export { PhysicalSlotMachine as SlotMachineCabinet };
