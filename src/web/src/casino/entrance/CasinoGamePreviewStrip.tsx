import { useNavigate } from "react-router-dom";
import { casinoSound } from "../casinoSound";
import { CARD_VISUALS } from "./cardVisuals";

export type PreviewCard = {
  id: string;
  title: string;
  status: string;
  to?: string;
  soon?: boolean;
};

export const ENTRANCE_PREVIEWS: PreviewCard[] = [
  { id: "roulette", title: "РУЛЕТКА", status: "LIVE", to: "/casino/roulette/royale-1" },
  { id: "blackjack", title: "BLACKJACK", status: "LIVE", to: "/casino/blackjack" },
  { id: "poker", title: "ПОКЕР", status: "LIVE", to: "/casino/poker" },
  { id: "slots", title: "АВТОМАТЫ", status: "SLOTS", to: "/casino/slots" },
  { id: "live", title: "LIVE КАЗИНО", status: "НОВИНКА", soon: true },
  { id: "tournaments", title: "ТУРНИРЫ", status: "ИГРАЙ И ВЫИГРЫВАЙ", soon: true },
];

export function CasinoGamePreviewStrip({
  onSoon,
}: {
  onSoon: (title: string) => void;
}) {
  const navigate = useNavigate();

  return (
    <div className="op-preview-strip" data-testid="casino-preview-strip">
      {ENTRANCE_PREVIEWS.map((card) => {
        const visual = CARD_VISUALS[card.id];
        return (
          <button
            key={card.id}
            type="button"
            className={`op-preview-card art-${card.id}`}
            data-testid={`preview-${card.id}`}
            aria-label={`${card.title}, ${card.status}${visual?.alt ? `. ${visual.alt}` : ""}`}
            onMouseEnter={() => casinoSound.hover()}
            onClick={() => {
              casinoSound.click();
              if (card.soon || !card.to) {
                onSoon(card.title);
                return;
              }
              navigate(card.to);
            }}
          >
            <span className="op-preview-visual">
              {visual ? (
                <img
                  className="op-preview-photo"
                  src={visual.src}
                  alt=""
                  width={320}
                  height={200}
                  loading="lazy"
                  decoding="async"
                  draggable={false}
                />
              ) : null}
              <span className="op-preview-art" aria-hidden>
                <PreviewArt kind={card.id} />
              </span>
              <span className="op-preview-shade" aria-hidden />
            </span>
            <span className="op-preview-copy">
              <strong>{card.title}</strong>
              <small>{card.status}</small>
            </span>
          </button>
        );
      })}
    </div>
  );
}

function PreviewArt({ kind }: { kind: string }) {
  if (kind === "roulette") {
    return (
      <svg viewBox="0 0 160 100" className="op-preview-svg" aria-hidden>
        <defs>
          <radialGradient id="rw" cx="50%" cy="48%" r="48%">
            <stop offset="0%" stopColor="#1a3d32" />
            <stop offset="70%" stopColor="#07140f" />
            <stop offset="100%" stopColor="#040806" />
          </radialGradient>
        </defs>
        <rect width="160" height="100" fill="#08110e" />
        <ellipse cx="80" cy="54" rx="58" ry="38" fill="#0a241c" stroke="#c9a45c" strokeWidth="1.2" />
        <ellipse cx="80" cy="52" rx="44" ry="30" fill="url(#rw)" stroke="#e8d5a3" strokeWidth="0.8" />
        <g stroke="#8c1c28" strokeWidth="2">
          <path d="M80 24 L86 52 L74 52 Z" fill="#8c1c28" stroke="none" />
          <path d="M80 24 L82 52" />
        </g>
        <circle cx="80" cy="52" r="9" fill="#c9a45c" />
        <circle cx="80" cy="52" r="3" fill="#1a140c" />
        <circle cx="118" cy="70" r="8" fill="#5a1820" stroke="#e8d5a3" />
        <circle cx="108" cy="78" r="7" fill="#1a140c" stroke="#c9a45c" />
      </svg>
    );
  }
  if (kind === "blackjack") {
    return (
      <svg viewBox="0 0 160 100" className="op-preview-svg" aria-hidden>
        <rect width="160" height="100" fill="#06281e" />
        <ellipse cx="80" cy="78" rx="70" ry="22" fill="#0b4a36" />
        <rect x="42" y="22" width="36" height="50" rx="4" fill="#f4ead7" transform="rotate(-16 60 47)" />
        <rect x="68" y="16" width="36" height="50" rx="4" fill="#f4ead7" />
        <text x="86" y="46" fill="#8c1c28" fontSize="16" fontFamily="Georgia, serif">
          A
        </text>
        <circle cx="124" cy="68" r="12" fill="#8c1c28" stroke="#e8d5a3" />
        <circle cx="112" cy="76" r="12" fill="#c9a45c" stroke="#1a140c" />
      </svg>
    );
  }
  if (kind === "poker") {
    return (
      <svg viewBox="0 0 160 100" className="op-preview-svg" aria-hidden>
        <rect width="160" height="100" fill="#051c16" />
        <ellipse cx="80" cy="62" rx="68" ry="28" fill="#07281e" stroke="#c9a45c" strokeWidth="0.8" />
        <rect x="28" y="30" width="26" height="36" rx="3" fill="#f4ead7" />
        <rect x="48" y="26" width="26" height="36" rx="3" fill="#f4ead7" />
        <rect x="68" y="28" width="26" height="36" rx="3" fill="#f4ead7" />
        <circle cx="112" cy="64" r="10" fill="#c9a45c" />
        <circle cx="126" cy="58" r="10" fill="#8c1c28" />
        <circle cx="118" cy="74" r="10" fill="#0d3b2e" stroke="#e8d5a3" />
      </svg>
    );
  }
  if (kind === "slots") {
    return (
      <svg viewBox="0 0 160 100" className="op-preview-svg" aria-hidden>
        <rect width="160" height="100" fill="#120e0a" />
        <rect x="38" y="8" width="84" height="84" rx="8" fill="#1a140c" stroke="#c9a45c" />
        <rect x="48" y="18" width="64" height="40" rx="4" fill="#0a1210" />
        <text x="80" y="46" textAnchor="middle" fill="#e8d5a3" fontSize="20" fontFamily="Georgia, serif">
          777
        </text>
        <circle cx="80" cy="76" r="8" fill="#8c1c28" stroke="#c9a45c" />
      </svg>
    );
  }
  if (kind === "live") {
    return (
      <svg viewBox="0 0 160 100" className="op-preview-svg" aria-hidden>
        <rect width="160" height="100" fill="#070b12" />
        <ellipse cx="80" cy="78" rx="62" ry="16" fill="#0d3b2e" />
        <rect x="50" y="18" width="60" height="42" rx="3" fill="#1c1610" stroke="#c9a45c" />
        <circle cx="80" cy="34" r="10" fill="#e8d5a3" />
        <rect x="62" y="46" width="36" height="10" fill="#3a2a18" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 160 100" className="op-preview-svg" aria-hidden>
      <rect width="160" height="100" fill="#14100c" />
      <path d="M80 14 L90 42 H118 L96 58 L106 86 L80 70 L54 86 L64 58 L42 42 H70 Z" fill="#c9a45c" />
      <ellipse cx="80" cy="86" rx="36" ry="6" fill="rgba(201,164,92,0.28)" />
    </svg>
  );
}
