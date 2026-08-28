import { Link } from "react-router-dom";
import { CASINO_ROUTES } from "../state/casinoRoutes";
import { DealerPortrait } from "../components/DealerPortrait";
import { RoomNavigation } from "../components/RoomNavigation";

export function RouletteHall() {
  return (
    <section className="op-room op-roulette-hall" data-testid="roulette-hall" aria-label="Зал рулетки">
      <div className="op-scene-live is-roulette" aria-hidden>
        <div className="op-scene-glow" />
        <div className="op-chandelier is-flicker" />
        <div className="op-lamp-pool" />
        <div className="op-hall-table" />
        <span className="op-wood-rail" />
        <span className="op-npc" />
        <div className="op-fog" />
      </div>
      <DealerPortrait />
      <div className="op-hero">
        <p className="op-kicker op-sign-shimmer">ROULETTE ROYALE</p>
        <h1 className="op-title">Европейская рулетка</h1>
        <p className="op-sub">Сядьте за стол · колесо и шар анимируются после серверного результата</p>
        <Link className="op-cta" to={CASINO_ROUTES.rouletteLive}>
          СЕСТЬ ЗА СТОЛ
        </Link>
        <RoomNavigation current="roulette" />
      </div>
    </section>
  );
}

export default RouletteHall;
