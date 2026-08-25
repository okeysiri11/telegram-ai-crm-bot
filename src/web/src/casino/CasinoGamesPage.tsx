import { Link } from "react-router-dom";

const GAMES = [
  { id: "roulette", title: "РУЛЕТКА", live: true, players: "LIVE", to: "/casino/rooms/roulette" },
  { id: "blackjack", title: "BLACKJACK", live: true, players: "LIVE", to: "/casino/rooms/blackjack" },
  { id: "slots", title: "ОДЕССА GOLD", live: true, players: "LIVE", to: "/casino/slots/odessa-gold" },
  { id: "poker", title: "ПОКЕР", live: true, players: "ЗАЛ", to: "/casino/rooms/poker" },
  { id: "vip", title: "VIP", live: true, players: "ЗАЛ", to: "/casino/rooms/vip" },
  { id: "bar", title: "БАР", live: true, players: "ЗАЛ", to: "/casino/rooms/bar" },
  { id: "restaurant", title: "РЕСТОРАН", live: true, players: "ЗАЛ", to: "/casino/rooms/restaurant" },
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
