import { Link } from "react-router-dom";
import { CASINO_ROUTES } from "../state/casinoRoutes";
import { DealerPortrait } from "../components/DealerPortrait";

export function RouletteHall() {
  return (
    <section className="op-room op-roulette-hall" data-testid="roulette-hall" aria-label="Зал рулетки">
      <div className="op-room-depth is-roulette">
        <div className="op-chandelier" />
        <DealerPortrait />
        <div className="op-hall-table" aria-hidden />
      </div>
      <div className="op-hero">
        <p className="op-kicker">ROULETTE ROYALE</p>
        <h1 className="op-title">Зал европейской рулетки</h1>
        <p className="op-sub">Крупье за столом · колесо и шар анимируются после серверного результата</p>
        <Link className="op-cta" to={CASINO_ROUTES.table("roulette-royale-1")}>
          СЕСТЬ ЗА СТОЛ
        </Link>
      </div>
    </section>
  );
}
