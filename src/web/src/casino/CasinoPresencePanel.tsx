import { Button } from "@/ui";
import type { CasinoRooms, CasinoTablePresence } from "./types";

export function CasinoPresencePanel({
  rooms,
  active,
  reconnecting,
  error,
  onJoin,
  onLeave,
  onReconnect,
}: {
  rooms: CasinoRooms | null;
  active: CasinoTablePresence | null;
  reconnecting: boolean;
  error: string | null;
  onJoin: (roomId: string) => void;
  onLeave: (roomId: string) => void;
  onReconnect: () => void;
}) {
  const tables = rooms?.tables ?? [];
  return (
    <section className="casino-presence" aria-label="Столы">
      <p className="casino-kicker">Присутствие</p>
      {reconnecting ? <p className="casino-status">Переподключение…</p> : null}
      {error ? (
        <p className="casino-status" role="alert">
          {error}{" "}
          <Button size="sm" variant="secondary" onClick={onReconnect}>
            Переподключить
          </Button>
        </p>
      ) : null}
      {!rooms && !error ? <p className="eds-type-helper">Загрузка столов…</p> : null}
      {tables.map((table) => (
        <article key={table.room_id} className="casino-table-card">
          <div className="casino-meta">
            <div>
              <div className="casino-kicker">СТОЛ</div>
              <strong>{table.table}</strong>
            </div>
            <div>
              <div className="casino-kicker">ИГРОКИ</div>
              <strong>
                {table.seats_taken} / {table.seats_total}
              </strong>
            </div>
            <div>
              <div className="casino-kicker">МЕСТА</div>
              <strong>{table.seats_total}</strong>
            </div>
            <div>
              <div className="casino-kicker">СТАТУС</div>
              <strong>{table.status_label}</strong>
            </div>
          </div>
          <div className="casino-seats" aria-label="Места за столом">
            {table.seats.map((seat) => (
              <span key={seat.seat} className="casino-seat">
                {seat.occupied ? seat.display_name : `Место ${seat.seat}`}
              </span>
            ))}
          </div>
          <div className="casino-actions" style={{ marginTop: "0.7rem" }}>
            {table.coming_soon ? (
              <Button size="sm" disabled>
                Скоро
              </Button>
            ) : active?.room_id === table.room_id ? (
              <Button size="sm" variant="secondary" onClick={() => onLeave(table.room_id)}>
                Покинуть стол
              </Button>
            ) : (
              <Button size="sm" onClick={() => onJoin(table.room_id)}>
                Сесть за стол
              </Button>
            )}
          </div>
        </article>
      ))}
    </section>
  );
}
