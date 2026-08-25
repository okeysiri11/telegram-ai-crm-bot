import { Link } from "react-router-dom";
import { CASINO_ROUTES } from "../state/casinoRoutes";

export function SlotParlor() {
  return (
    <section className="op-room op-slot-room" data-testid="slots-room" aria-label="Зал автоматов">
      <div className="op-slot-row">
        {["ODESSA GOLD", "BLACK SEA", "PRIMORSKY"].map((name, i) => (
          <article key={name} className={`op-slot-cabinet${i === 0 ? " is-live" : ""}`}>
            <div className="op-slot-screen" />
            <strong>{name}</strong>
            {i === 0 ? (
              <Link className="op-cta" to={CASINO_ROUTES.slot("odessa-gold")}>
                ИГРАТЬ
              </Link>
            ) : (
              <span className="op-status">Скоро</span>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
