import { useNavigate } from "react-router-dom";
import { casinoSound } from "../casinoSound";

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
      {ENTRANCE_PREVIEWS.map((card) => (
        <button
          key={card.id}
          type="button"
          className={`op-preview-card art-${card.id}`}
          data-testid={`preview-${card.id}`}
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
          <span className="op-preview-art" aria-hidden>
            <PreviewArt kind={card.id} />
          </span>
          <span className="op-preview-copy">
            <strong>{card.title}</strong>
            <small>{card.status}</small>
          </span>
        </button>
      ))}
    </div>
  );
}

function PreviewArt({ kind }: { kind: string }) {
  if (kind === "roulette") {
    return (
      <svg viewBox="0 0 160 90" className="op-preview-svg">
        <rect width="160" height="90" fill="#0b1a14" />
        <ellipse cx="80" cy="48" rx="46" ry="46" fill="#1a140c" stroke="#c9a45c" />
        <ellipse cx="80" cy="48" rx="28" ry="28" fill="#0d3b2e" stroke="#e8d5a3" />
        <circle cx="80" cy="48" r="8" fill="#c9a45c" />
        <path d="M80 20 L84 48 L76 48 Z" fill="#8c1c28" />
      </svg>
    );
  }
  if (kind === "blackjack") {
    return (
      <svg viewBox="0 0 160 90" className="op-preview-svg">
        <rect width="160" height="90" fill="#0b4a36" />
        <rect x="38" y="22" width="38" height="52" rx="4" fill="#f4ead7" transform="rotate(-12 57 48)" />
        <rect x="70" y="18" width="38" height="52" rx="4" fill="#f4ead7" />
        <circle cx="128" cy="62" r="14" fill="#8c1c28" stroke="#e8d5a3" />
        <circle cx="118" cy="68" r="14" fill="#1a140c" stroke="#c9a45c" />
      </svg>
    );
  }
  if (kind === "poker") {
    return (
      <svg viewBox="0 0 160 90" className="op-preview-svg">
        <rect width="160" height="90" fill="#07281e" />
        <rect x="24" y="28" width="28" height="40" rx="3" fill="#f4ead7" />
        <rect x="48" y="24" width="28" height="40" rx="3" fill="#f4ead7" />
        <circle cx="108" cy="58" r="12" fill="#c9a45c" />
        <circle cx="124" cy="50" r="12" fill="#8c1c28" />
        <circle cx="118" cy="68" r="12" fill="#0d3b2e" stroke="#e8d5a3" />
      </svg>
    );
  }
  if (kind === "slots") {
    return (
      <svg viewBox="0 0 160 90" className="op-preview-svg">
        <rect width="160" height="90" fill="#12100c" />
        <rect x="36" y="12" width="88" height="66" rx="6" fill="#1a140c" stroke="#c9a45c" />
        <text x="80" y="56" textAnchor="middle" fill="#e8d5a3" fontSize="22" fontFamily="Georgia, serif">
          777
        </text>
      </svg>
    );
  }
  if (kind === "live") {
    return (
      <svg viewBox="0 0 160 90" className="op-preview-svg">
        <rect width="160" height="90" fill="#0a1018" />
        <ellipse cx="80" cy="70" rx="58" ry="16" fill="#0d3b2e" />
        <rect x="58" y="22" width="44" height="36" fill="#1c1610" stroke="#c9a45c" />
        <circle cx="80" cy="34" r="8" fill="#e8d5a3" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 160 90" className="op-preview-svg">
      <rect width="160" height="90" fill="#16120c" />
      <path d="M80 16 L88 40 H112 L92 54 L100 78 L80 64 L60 78 L68 54 L48 40 H72 Z" fill="#c9a45c" />
    </svg>
  );
}
