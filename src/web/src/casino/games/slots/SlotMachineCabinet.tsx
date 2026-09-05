import type { CSSProperties } from "react";
import { Link } from "react-router-dom";
import { CASINO_ROUTES } from "../../state/casinoRoutes";
import { symbolLabel } from "./slotCatalog";
import type { SlotGameDefinition } from "./slotTypes";

type Props = {
  def: SlotGameDefinition;
  favorite?: boolean;
  onFavorite?: (id: string) => void;
};

export function SlotMachineCabinet({ def, favorite, onFavorite }: Props) {
  const preview = def.symbols.slice(0, 3);
  return (
    <article
      className={`op-hall-cabinet theme-${def.theme}`}
      data-testid={`slot-cabinet-${def.id}`}
      style={{ "--cab-accent": def.accent, "--cab-accent-2": def.accent2 } as CSSProperties}
    >
      <div className="op-hall-cabinet-top" aria-hidden>
        <span className="op-hall-marquee">{def.title}</span>
      </div>
      <div className="op-hall-cabinet-body">
        <div className="op-hall-cabinet-screen" data-testid={`slot-preview-${def.id}`}>
          <div className="op-hall-preview">
            {preview.map((sym) => (
              <span key={sym.id}>{symbolLabel(def, sym.id)}</span>
            ))}
          </div>
        </div>
        <div className="op-hall-cabinet-mid">
          <strong>{def.title}</strong>
          <span className="op-hall-provider">{def.provider}</span>
        </div>
        <div className="op-hall-cabinet-controls" aria-hidden>
          <i />
          <i />
          <i />
        </div>
        <div className="op-hall-cabinet-actions">
          <button
            type="button"
            className={`op-hall-fav${favorite ? " is-on" : ""}`}
            aria-label="Избранное"
            onClick={() => onFavorite?.(def.id)}
          >
            {favorite ? "★" : "☆"}
          </button>
          <Link className="op-cta op-hall-play" to={CASINO_ROUTES.slot(def.slug)} data-testid={`slot-play-${def.id}`}>
            Играть
          </Link>
        </div>
      </div>
      <div className="op-hall-cabinet-base" aria-hidden>
        <span className="op-hall-chair" />
      </div>
    </article>
  );
}
