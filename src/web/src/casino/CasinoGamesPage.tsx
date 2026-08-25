import { Link } from "react-router-dom";
import { ROOM_CATALOG } from "./state/casinoRoutes";

export function CasinoGamesPage() {
  return (
    <div className="op-games">
      {ROOM_CATALOG.filter((r) => r.id !== "lobby").map((game) => (
        <Link key={game.id} className={`op-game is-${game.id}`} to={game.route} aria-label={game.label}>
          <span className="op-badge">LIVE</span>
          <h3>{game.label}</h3>
          <p>Открыто · PLAY</p>
        </Link>
      ))}
    </div>
  );
}
