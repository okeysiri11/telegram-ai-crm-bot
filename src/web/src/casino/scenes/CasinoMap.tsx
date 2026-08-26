import { useLocation } from "react-router-dom";
import { casinoSound } from "../casinoSound";
import { useRoomTransition } from "../transitions/useRoomTransition";
import { LOBBY_HOTSPOTS, mapZoneIsHere } from "../lobby/hotspots";
import { CASINO_ROUTES } from "../state/casinoRoutes";

export function CasinoMap() {
  const { go } = useRoomTransition();
  const location = useLocation();
  const path = location.pathname;

  return (
    <div className="op-map op-world-map op-floorplan" data-testid="casino-map" aria-label="Карта казино">
      <div className="op-floorplan-stage">
        <p className="op-floorplan-title">План этажа · Odessa Prime</p>
        <button
          type="button"
          className={`op-map-zone is-lobby${mapZoneIsHere(CASINO_ROUTES.lobbyAlias, path, "lobby") ? " is-here" : ""}`}
          style={{ left: "32%", top: "38%", width: "36%", height: "22%" }}
          data-testid="map-zone-lobby"
          aria-label="ЛОББИ: открыто"
          onMouseEnter={() => casinoSound.hover()}
          onClick={() => {
            casinoSound.click();
            go(CASINO_ROUTES.lobbyAlias);
          }}
        >
          <small>ВЫ ЗДЕСЬ</small>
          <strong>ЛОББИ</strong>
        </button>
        {LOBBY_HOTSPOTS.map((spot) => (
          <button
            key={spot.id}
            type="button"
            className={`op-map-zone is-${spot.id}${mapZoneIsHere(spot.to, path, spot.id) ? " is-here" : ""}`}
            style={{
              left: `${spot.map.x / 10}%`,
              top: `${spot.map.y / 6.4}%`,
              width: `${spot.map.w / 10}%`,
              height: `${spot.map.h / 6.4}%`,
            }}
            data-testid={`map-zone-${spot.id}`}
            aria-label={`${spot.label}: открыто`}
            onMouseEnter={() => casinoSound.hover()}
            onClick={() => {
              casinoSound.door();
              go(spot.to);
            }}
          >
            <small>OPEN</small>
            <strong>{spot.label}</strong>
          </button>
        ))}
      </div>
    </div>
  );
}
