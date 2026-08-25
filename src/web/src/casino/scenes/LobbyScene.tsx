import { useState } from "react";
import { ROOM_CATALOG } from "../state/casinoRoutes";
import { useRoomTransition } from "../transitions/useRoomTransition";
import { CasinoMap } from "./CasinoMap";

const HOTSPOTS = [
  { id: "vip", label: "VIP", x: "6%", y: "14%", w: "16%", h: "18%", to: "/casino/vip", cta: "ВОЙТИ" },
  { id: "restaurant", label: "РЕСТОРАН", x: "28%", y: "12%", w: "20%", h: "16%", to: "/casino/restaurant", cta: "ВОЙТИ" },
  { id: "bar", label: "БАР", x: "78%", y: "12%", w: "16%", h: "18%", to: "/casino/bar", cta: "ВОЙТИ" },
  { id: "poker", label: "ПОКЕР", x: "52%", y: "16%", w: "20%", h: "16%", to: "/casino/poker", cta: "ВОЙТИ" },
  { id: "roulette", label: "РУЛЕТКА", x: "12%", y: "42%", w: "28%", h: "30%", to: "/casino/roulette/royale-1", cta: "СЕСТЬ ЗА СТОЛ" },
  { id: "blackjack", label: "BLACKJACK", x: "44%", y: "40%", w: "24%", h: "28%", to: "/casino/blackjack", cta: "СЕСТЬ ЗА СТОЛ" },
  { id: "slots", label: "ОДЕССА GOLD", x: "70%", y: "46%", w: "24%", h: "28%", to: "/casino/slots", cta: "ИГРАТЬ" },
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
            <div className="op-chandelier is-flicker is-lobby" aria-hidden />
            <div className="op-room-carpet" aria-hidden />
            <span className="op-npc" aria-hidden />
            <span className="op-npc is-2" aria-hidden />
            {HOTSPOTS.map((spot) => (
              <button
                key={spot.id}
                type="button"
                className="op-hotspot is-live"
                style={{ left: spot.x, top: spot.y, width: spot.w, height: spot.h }}
                data-testid={`hotspot-${spot.id}`}
                aria-label={`${spot.label}: ${spot.cta}`}
                onClick={() => go(spot.to)}
              >
                <span className="op-hotspot-glow" aria-hidden />
                <small>{spot.cta}</small>
                <strong>{spot.label}</strong>
              </button>
            ))}
          </div>
        </div>
      )}
      <p className="op-status">Наведите на зону — зал вспыхнет золотом, появится действие.</p>
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
