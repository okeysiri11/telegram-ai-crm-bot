import { RoomNavigation } from "../components/RoomNavigation";

export type AtmosphereKind = "poker" | "vip" | "restaurant" | "bar";

const COPY: Record<AtmosphereKind, { title: string; kicker: string; testid: string; label: string; room: AtmosphereKind }> = {
  poker: { title: "POKER ROOM", kicker: "ПРИМОРСКИЙ · FELT", testid: "poker-room", label: "Покерный зал Odessa Prime", room: "poker" },
  vip: { title: "VIP SALON", kicker: "MONACO · PRIVATE", testid: "vip-room", label: "VIP зона Odessa Prime", room: "vip" },
  restaurant: { title: "RESTAURANT", kicker: "ODESSA · DINING", testid: "restaurant-room", label: "Ресторан Odessa Prime", room: "restaurant" },
  bar: { title: "THE BAR", kicker: "BLACK SEA · NIGHT", testid: "bar-room", label: "Бар Odessa Prime", room: "bar" },
};

export function AtmosphereRoom({ kind }: { kind: AtmosphereKind }) {
  const copy = COPY[kind];
  return (
    <section className={`op-room op-atmo is-${kind}`} data-testid={copy.testid} aria-label={copy.label}>
      <div className={`op-scene-live is-${kind}`} aria-hidden>
        <div className="op-scene-glow" />
        <div className="op-chandelier is-flicker" />
        <div className="op-lamp-pool" />
        <div className="op-fog" />
        {kind === "bar" ? <BarSet /> : null}
        {kind === "restaurant" ? <RestaurantSet /> : null}
        {kind === "vip" ? <VipSet /> : null}
        {kind === "poker" ? <PokerSet /> : null}
        <span className="op-npc" />
        <span className="op-npc is-2" />
      </div>
      <div className="op-atmo-caption">
        <p className="op-kicker op-sign-shimmer">{copy.kicker}</p>
        <h1 className="op-title">{copy.title}</h1>
        <RoomNavigation current={kind} />
      </div>
    </section>
  );
}

function BarSet() {
  return (
    <div className="op-bar-set">
      <div className="op-bar-shelf">
        {Array.from({ length: 10 }, (_, i) => (
          <span key={i} className="op-bottle" style={{ animationDelay: `${i * 0.4}s` }} />
        ))}
      </div>
      <div className="op-bar-counter" />
      <div className="op-stools">
        <span />
        <span />
        <span />
        <span />
      </div>
    </div>
  );
}

function RestaurantSet() {
  return (
    <div className="op-rest-set">
      {Array.from({ length: 6 }, (_, i) => (
        <div key={i} className="op-dine" style={{ left: `${12 + (i % 3) * 28}%`, top: `${28 + Math.floor(i / 3) * 32}%` }}>
          <span className="op-lamp" />
          <span className="op-cloth" />
        </div>
      ))}
    </div>
  );
}

function VipSet() {
  return (
    <div className="op-vip-set">
      <div className="op-vip-drape" />
      <div className="op-vip-table is-a" />
      <div className="op-vip-table is-b" />
      <div className="op-vip-sofa" />
    </div>
  );
}

function PokerSet() {
  return (
    <div className="op-poker-set">
      <div className="op-poker-felt" />
      {Array.from({ length: 6 }, (_, i) => (
        <span key={i} className="op-poker-seat" style={{ transform: `rotate(${i * 60}deg) translateY(-7.2rem)` }} />
      ))}
    </div>
  );
}
