import { useState } from "react";
import { LobbyHall } from "../lobby/LobbyHall";
import { CasinoMap } from "./CasinoMap";

export function LobbyScene({ view = "hall" }: { view?: "hall" | "map" }) {
  const [mode, setMode] = useState<"hall" | "map">(view);

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
            <LobbyHall />
          </div>
        </div>
      )}
      <p className="op-status op-hall-hint">Исследуйте зал. Наведите на зону — она подсветится. Нажмите, чтобы войти.</p>
    </div>
  );
}
