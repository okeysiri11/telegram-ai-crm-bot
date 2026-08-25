import { useState } from "react";
import { ROOM_CATALOG } from "../state/casinoRoutes";
import { useRoomTransition } from "../transitions/useRoomTransition";
import { CasinoMap } from "./CasinoMap";

const HOTSPOTS = [
  { id: "vip", label: "VIP", live: true, x: "6%", y: "14%", w: "16%", h: "18%", to: "/casino/rooms/vip" },
  { id: "restaurant", label: "РЕСТОРАН", live: true, x: "28%", y: "12%", w: "20%", h: "16%", to: "/casino/rooms/restaurant" },
  { id: "bar", label: "БАР", live: true, x: "78%", y: "12%", w: "16%", h: "18%", to: "/casino/rooms/bar" },
  { id: "poker", label: "ПОКЕР", live: true, x: "52%", y: "16%", w: "20%", h: "16%", to: "/casino/rooms/poker" },
  { id: "roulette", label: "РУЛЕТКА", live: true, x: "12%", y: "42%", w: "28%", h: "30%", to: "/casino/rooms/roulette" },
  { id: "blackjack", label: "BLACKJACK", live: true, x: "44%", y: "40%", w: "24%", h: "28%", to: "/casino/rooms/blackjack" },
  { id: "slots", label: "ОДЕССА GOLD", live: true, x: "70%", y: "46%", w: "24%", h: "28%", to: "/casino/rooms/slots" },
] as const;

export function LobbyScene() {
  const { go } = useRoomTransition();
  const [mode, setMode] = useState<"hall" | "map">("hall");

  return (
    <div className="op-lobby-room" data-testid="casino-lobby" aria-label="Главный зал Odessa Prime">
      <div className="op-toolbar">
        <h1 className="op-kicker op-sign-shimmer">Зал Odessa Prime</h1>
        <div className="op-toggle" role="group" aria-label="Вид зала">
          <button type="button" className={mode === "hall" ? "is-on" : undefined} onClick={() => setMode("hall")}>
            ЗАЛ
          </button>
          <button type="button" className={mode === "map" ? "is-on" : undefined} onClick={() => setMode("map")}>
            КАРТА
          </button>
        </div>
      </div>
      {mode === "map" ? (
        <CasinoMap />
      ) : (
        <div className="op-lobby-pan" data-testid="lobby-pan">
          <div className="op-room-depth op-lobby-stage">
            <div className="op-room-ceiling" aria-hidden />
            <div className="op-room-backwall" aria-hidden />
            <div className="op-chandelier is-lobby" aria-hidden />
            <div className="op-room-carpet" aria-hidden />
            {HOTSPOTS.map((spot) => (
              <button
                key={spot.id}
                type="button"
                className={`op-hotspot${spot.live ? " is-live" : " is-soon"}`}
                style={{ left: spot.x, top: spot.y, width: spot.w, height: spot.h }}
                data-testid={`hotspot-${spot.id}`}
                aria-label={`${spot.label}: войти`}
                onClick={() => go(spot.to)}
              >
                <span className="op-hotspot-glow" aria-hidden />
                <small>ВОЙТИ</small>
                <strong>{spot.label}</strong>
              </button>
            ))}
          </div>
        </div>
      )}
      <p className="op-status">Горячие зоны светятся золотом — переход в комнату без смены chrome.</p>
      <div className="op-room-links">
        {ROOM_CATALOG.filter((r) => r.id !== "lobby").map((room) => (
          <button key={room.id} className="op-cta secondary" type="button" onClick={() => go(room.route)}>
            {room.label}
          </button>
        ))}
      </div>
    </div>
  );
}
