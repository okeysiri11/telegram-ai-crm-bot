import { Link } from "react-router-dom";
import { CASINO_ROUTES, ROOM_CATALOG, ROOM_CYCLE, type CasinoRoomId } from "../state/casinoRoutes";
import { useRoomTransition } from "../transitions/useRoomTransition";

export function RoomNavigation({ current }: { current: CasinoRoomId }) {
  const { go } = useRoomTransition();
  const idx = Math.max(0, ROOM_CYCLE.indexOf(current));
  const nextId = ROOM_CYCLE[(idx + 1) % ROOM_CYCLE.length];
  const next = ROOM_CATALOG.find((r) => r.id === nextId);
  return (
    <nav className="op-room-nav" aria-label="Навигация зала">
      <button className="op-ghost" type="button" onClick={() => go(CASINO_ROUTES.lobbyAlias)}>
        ← В ЗАЛ
      </button>
      <Link className="op-ghost" to={CASINO_ROUTES.map}>
        КАРТА
      </Link>
      {next ? (
        <button className="op-cta secondary" type="button" onClick={() => go(next.route)}>
          ДАЛЕЕ · {next.label}
        </button>
      ) : null}
    </nav>
  );
}
