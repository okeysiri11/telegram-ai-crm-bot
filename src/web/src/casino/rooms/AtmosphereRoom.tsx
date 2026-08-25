import { Link } from "react-router-dom";
import { CASINO_ROUTES } from "../state/casinoRoutes";

export type AtmosphereKind = "poker" | "vip" | "restaurant" | "bar";

const COPY: Record<
  AtmosphereKind,
  { title: string; kicker: string; sub: string; testid: string; label: string; cta: string }
> = {
  poker: {
    title: "POKER ROOM",
    kicker: "ПРИМОРСКИЙ · FELT",
    sub: "Атмосфера живого стола. Раздача и банк — Sprint 20. Только PLAY / DEMO CHIPS.",
    testid: "poker-room",
    label: "Покерный зал Odessa Prime",
    cta: "К СТОЛАМ",
  },
  vip: {
    title: "VIP SALON",
    kicker: "MONACO · PRIVATE",
    sub: "Закрытый салон. Высокие лимиты и живой стол — позже. Сейчас — атмосфера зала.",
    testid: "vip-room",
    label: "VIP зона Odessa Prime",
    cta: "В ЗАЛ",
  },
  restaurant: {
    title: "RESTAURANT",
    kicker: "ODESSA · DINING",
    sub: "Ресторан казино. Меню и бронь — позже. Можно войти, осмотреть зал и вернуться.",
    testid: "restaurant-room",
    label: "Ресторан Odessa Prime",
    cta: "В ЗАЛ",
  },
  bar: {
    title: "THE BAR",
    kicker: "BLACK SEA · NIGHT",
    sub: "Бар у зала. Живая атмосфера, без автозапуска звука. Заказ напитков — позже.",
    testid: "bar-room",
    label: "Бар Odessa Prime",
    cta: "В ЗАЛ",
  },
};

export function AtmosphereRoom({ kind }: { kind: AtmosphereKind }) {
  const copy = COPY[kind];
  return (
    <section className={`op-room op-atmo is-${kind}`} data-testid={copy.testid} aria-label={copy.label}>
      <div className={`op-room-depth is-${kind}`} aria-hidden>
        <div className="op-chandelier" />
        <div className="op-atmo-set" />
        <span className="op-reflect" />
      </div>
      <div className="op-hero">
        <p className="op-kicker op-sign-shimmer">{copy.kicker}</p>
        <h1 className="op-title">{copy.title}</h1>
        <p className="op-sub">{copy.sub}</p>
        <Link className="op-cta" to={CASINO_ROUTES.floor}>
          {copy.cta}
        </Link>
      </div>
    </section>
  );
}
