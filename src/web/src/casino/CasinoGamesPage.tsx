import { Link } from "react-router-dom";

const GAMES = [
  { id: "roulette", title: "РУЛЕТКА", live: true, players: "LIVE", to: "/casino/roulette" },
  { id: "blackjack", title: "BLACKJACK", live: false, players: "Скоро", to: "/casino/games" },
  { id: "poker", title: "ПОКЕР", live: false, players: "Скоро", to: "/casino/games" },
  { id: "slots", title: "АВТОМАТЫ", live: false, players: "Скоро", to: "/casino/games" },
  { id: "live", title: "LIVE CASINO", live: false, players: "Скоро", to: "/casino/games" },
  { id: "tournaments", title: "ТУРНИРЫ", live: false, players: "Скоро", to: "/casino/games" },
];

export function CasinoGamesPage() {
  return (
    <div className="op-games">
      {GAMES.map((game) => (
        <Link key={game.id} className="op-game" to={game.to} aria-label={game.title}>
          <span className="op-badge">{game.live ? "LIVE" : "SOON"}</span>
          <h3>{game.title}</h3>
          <p>{game.players}</p>
          <span>{game.live ? "Войти" : "Скоро"}</span>
        </Link>
      ))}
    </div>
  );
}
