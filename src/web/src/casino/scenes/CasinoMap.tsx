import { ROOM_CATALOG } from "../state/casinoRoutes";
import { useRoomTransition } from "../transitions/useRoomTransition";

export function CasinoMap() {
  const { go, path } = useRoomTransition();
  return (
    <div className="op-map op-world-map" data-testid="casino-map" aria-label="Карта казино">
      {ROOM_CATALOG.map((room) => (
        <button
          key={room.id}
          type="button"
          className={`op-map-cell${path.startsWith(room.route) ? " is-here" : ""}`}
          aria-label={`${room.label}: ${room.live ? "открыто" : "скоро"}`}
          onClick={() => go(room.route)}
        >
          <small className="op-kicker">{room.live ? "OPEN" : "СКОРО"}</small>
          <div>{room.label}</div>
        </button>
      ))}
    </div>
  );
}
