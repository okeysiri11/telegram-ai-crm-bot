import { useState } from "react";
import { ROOM_CATALOG } from "../state/casinoRoutes";
import { useRoomTransition } from "../transitions/useRoomTransition";
import { CasinoMap } from "./CasinoMap";

const HOTSPOTS = [
  { id: "roulette", label: "РУЛЕТКА", live: true, x: "18%", y: "42%", w: "28%", h: "28%", to: "/casino/rooms/roulette" },
  { id: "blackjack", label: "BLACKJACK", live: true, x: "52%", y: "38%", w: "24%", h: "26%", to: "/casino/rooms/blackjack" },
  { id: "slots", label: "ОДЕССА GOLD", live: true, x: "72%", y: "48%", w: "22%", h: "24%", to: "/casino/rooms/slots" },
  { id: "vip", label: "VIP", live: false, x: "8%", y: "18%", w: "16%", h: "18%", to: "/casino/floor" },
] as const;

export function LobbyScene() {
  const { go } = useRoomTransition();
  const [mode, setMode] = useState<"hall" | "map">("hall");

  return (
    <div className="op-lobby-room" data-testid="casino-lobby" aria-label="Главный зал Odessa Prime">
      <div className="op-toolbar">
        <h1 className="op-kicker">Зал Odessa Prime</h1>
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
        <div className="op-room-depth">
          <div className="op-room-ceiling" />
          <div className="op-room-backwall" />
          <div className="op-chandelier is-lobby" />
          <div className="op-room-carpet" />
          {HOTSPOTS.map((spot) => (
            <button
              key={spot.id}
              type="button"
              className={`op-hotspot${spot.live ? " is-live" : " is-soon"}`}
              style={{ left: spot.x, top: spot.y, width: spot.w, height: spot.h }}
              data-testid={`hotspot-${spot.id}`}
              onClick={() => (spot.live ? go(spot.to) : undefined)}
            >
              <span className="op-hotspot-glow" />
              <small>{spot.live ? "ВОЙТИ" : "СКОРО"}</small>
              <strong>{spot.label}</strong>
            </button>
          ))}
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
