import { Link } from "react-router-dom";
import { CASINO_ROUTES } from "../state/casinoRoutes";
import { RoomNavigation } from "../components/RoomNavigation";

export function SlotParlor() {
  return (
    <section className="op-room op-slot-room" data-testid="slots-room" aria-label="Зал автоматов">
      <div className="op-scene-live is-slots" aria-hidden>
        <div className="op-scene-glow" />
        <div className="op-chandelier is-flicker" />
        <div className="op-lamp-pool" />
        <div className="op-fog" />
      </div>
      <div className="op-slot-row">
        <article className="op-slot-cabinet is-live">
          <div className="op-slot-screen is-lit" />
          <strong>ODESSA GOLD</strong>
          <Link className="op-cta" to={CASINO_ROUTES.slot("odessa-gold")}>
            ИГРАТЬ
          </Link>
        </article>
        <article className="op-slot-cabinet">
          <div className="op-slot-screen" />
          <strong>BLACK SEA</strong>
          <span className="op-status">Атмосфера зала · автомат позже</span>
        </article>
        <article className="op-slot-cabinet">
          <div className="op-slot-screen" />
          <strong>PRIMORSKY</strong>
          <span className="op-status">Атмосфера зала · автомат позже</span>
        </article>
      </div>
      <RoomNavigation current="slots" />
    </section>
  );
}

export default SlotParlor;
