import { useState } from "react";
import { casinoSound } from "../casinoSound";
import { useRoomTransition } from "../transitions/useRoomTransition";
import { CasinoMap } from "./CasinoMap";
import { LOBBY_HOTSPOTS } from "../lobby/hotspots";

export function LobbyScene({ view = "hall" }: { view?: "hall" | "map" }) {
  const { go } = useRoomTransition();
  const [mode, setMode] = useState<"hall" | "map">(view);
  const [lit, setLit] = useState<string | null>(null);

  return (
    <div className="op-lobby-room op-lobby-immersive" data-testid="casino-lobby" aria-label="Главный зал Odessa Prime">
      <div className="op-toolbar">
        <h1 className="op-kicker op-sign-shimmer">Главный зал · Odessa Prime</h1>
        <div className="op-toggle" role="group" aria-label="Вид зала">
          <button
            type="button"
            data-testid="lobby-toggle-hall"
            className={mode === "hall" ? "is-on" : undefined}
            onClick={() => setMode("hall")}
          >
            ЗАЛ
          </button>
          <button
            type="button"
            data-testid="lobby-toggle-map"
            className={mode === "map" ? "is-on" : undefined}
            onClick={() => setMode("map")}
          >
            КАРТА
          </button>
        </div>
      </div>
      {mode === "map" ? (
        <CasinoMap />
      ) : (
        <div className="op-lobby-pan" data-testid="lobby-pan">
          <div className="op-lobby-hall" data-testid="lobby-hall">
            <div className="op-lobby-photo" aria-hidden />
            <div className="op-lobby-vignette" aria-hidden />
            <div className="op-room-ceiling" aria-hidden />
            <div className="op-chandelier is-flicker is-lobby" aria-hidden />
            <div className="op-lamp-pool" aria-hidden />
            <div className="op-lobby-columns" aria-hidden>
              <span />
              <span />
              <span />
              <span />
            </div>
            <div className="op-room-carpet" aria-hidden />
            <div className="op-marble-sheen" aria-hidden />
            <div className="op-fog" aria-hidden />
            <span className="op-npc" aria-hidden />
            <span className="op-npc is-2" aria-hidden />
            <span className="op-npc is-3" aria-hidden />
            {LOBBY_HOTSPOTS.map((spot) => (
              <button
                key={spot.id}
                type="button"
                className={`op-hotspot is-live is-${spot.id}${lit === spot.id ? " is-lit" : ""}`}
                style={{ left: spot.x, top: spot.y, width: spot.w, height: spot.h }}
                data-testid={`hotspot-${spot.id}`}
                aria-label={`${spot.label}: ${spot.cta}`}
                onMouseEnter={() => {
                  setLit(spot.id);
                  casinoSound.hover();
                }}
                onMouseLeave={() => setLit((cur) => (cur === spot.id ? null : cur))}
                onFocus={() => setLit(spot.id)}
                onBlur={() => setLit((cur) => (cur === spot.id ? null : cur))}
                onClick={() => {
                  casinoSound.door();
                  go(spot.to);
                }}
              >
                <span className="op-hotspot-glow" aria-hidden />
                <span className="op-hotspot-preview">
                  <small>{spot.cta}</small>
                  <strong>{spot.label}</strong>
                  <em>{spot.venue}</em>
                  <span>{spot.detail}</span>
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
      <p className="op-status">Наведите на зону — зал вспыхнет золотом. Нажмите, чтобы войти.</p>
    </div>
  );
}
