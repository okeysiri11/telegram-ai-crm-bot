import { useRoomTransition } from "./transitions/useRoomTransition";
import { LOBBY_HOTSPOTS } from "./lobby/hotspots";
import { casinoSound } from "./casinoSound";

export function CasinoGamesPage() {
  const { go } = useRoomTransition();
  return (
    <div className="op-games op-games-hall" data-testid="casino-halls">
      {LOBBY_HOTSPOTS.map((game) => (
        <button
          key={game.id}
          type="button"
          className={`op-game is-${game.id}`}
          data-testid={`hall-card-${game.id}`}
          aria-label={game.label}
          onMouseEnter={() => casinoSound.hover()}
          onClick={() => {
            casinoSound.click();
            go(game.to);
          }}
        >
          <span className="op-badge">LIVE</span>
          <h3>{game.label}</h3>
          <p>
            {game.venue} · {game.detail}
          </p>
        </button>
      ))}
    </div>
  );
}
