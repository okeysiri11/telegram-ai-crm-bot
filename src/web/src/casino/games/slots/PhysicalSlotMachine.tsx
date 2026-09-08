import type { CSSProperties, MouseEvent } from "react";
import { Link } from "react-router-dom";
import { CASINO_ROUTES } from "../../state/casinoRoutes";
import { symbolLabel } from "./slotCatalog";
import { cabinetAspectRatio, cabinetImageUrl, cabinetScreenRect, CHAIR_URL } from "./cabinetAssets";
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
    <img
      className="op-phys-chair-img"
      src={CHAIR_URL}
      alt=""
      aria-hidden
      loading="lazy"
      decoding="async"
    />
  );
}

export function PhysicalSlotMachine({ def, index, selected, onSelect }: Props) {
  const href = CASINO_ROUTES.slot(def.slug);
  const grid = reelGrid(def);
  const cabinetImg = cabinetImageUrl(def);
  const screen = cabinetScreenRect(def);
  const cabStyle: CSSProperties = {
    aspectRatio: cabinetAspectRatio(def),
    "--cab-accent": def.accent,
    "--cab-accent-2": def.accent2,
  } as CSSProperties;
  const screenStyle: CSSProperties = {
    left: `${screen.leftPct}%`,
    top: `${screen.topPct}%`,
    width: `${screen.widthPct}%`,
    height: `${screen.heightPct}%`,
  };

  return (
    <article
      className={`op-phys-cab variant-${def.cabinetVariant} theme-${def.theme} pos-${index}${selected ? " is-selected" : ""}`}
      data-testid={`slot-cabinet-${def.id}`}
      data-variant={def.cabinetVariant}
      style={cabStyle}
    >
      <img className="op-phys-reflect" src={cabinetImg} alt="" aria-hidden loading="lazy" decoding="async" />
      <Link
        className="op-phys-hit"
        to={href}
        aria-label={`${def.title}. Джекпот ${def.jackpot}. Играть.`}
        data-testid={`slot-play-${def.id}`}
        onClick={(event) => onSelect?.(def.id, href, event)}
      >
        <div className="op-phys-art-wrap">
          <img
            className="op-phys-cabinet-img"
            src={cabinetImg}
            alt=""
            aria-hidden
            loading="lazy"
            decoding="async"
            data-testid={`slot-cabinet-asset-${def.id}`}
          />
          <div className="op-phys-glow" aria-hidden />
          <div className="op-phys-crown-glow" aria-hidden />
          <div className="op-phys-screen" data-testid={`slot-preview-${def.id}`} style={screenStyle}>
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
          <header className="op-phys-topper" data-testid={`slot-topper-${def.id}`} aria-hidden>
            <span className="sr-only">
              {def.title} — джекпот {def.jackpot}
            </span>
          </header>
          <div className="op-phys-panel-a11y sr-only" data-testid={`slot-controls-${def.id}`} aria-hidden>
            <span>BET −</span>
            <span>BET +</span>
            <span className="op-phys-spin">SPIN</span>
            <span>MAX</span>
            <span>INFO</span>
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
