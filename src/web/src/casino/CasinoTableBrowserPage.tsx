import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchCasinoRooms } from "./casinoApi";
import type { CasinoTablePresence } from "./types";

const CATALOG = [
  { id: "roulette-royale-1", name: "Roulette Royale 1", live: true, min: 10, max: 5000, seats: 6 },
  { id: "roulette-classic", name: "Roulette Classic", live: false, min: 10, max: 1000, seats: 6 },
  { id: "roulette-monaco", name: "Roulette Monaco", live: false, min: 50, max: 5000, seats: 8 },
  { id: "roulette-vip", name: "Roulette VIP", live: false, min: 500, max: 5000, seats: 4 },
];

export function CasinoTableBrowserPage() {
  const [rooms, setRooms] = useState<CasinoTablePresence[]>([]);

  useEffect(() => {
    fetchCasinoRooms("odessa-prime")
      .then((payload) => setRooms(payload.tables.filter((t) => t.game === "roulette")))
      .catch(() => undefined);
  }, []);

  return (
    <div className="op-tables">
      <h1 className="op-kicker">Столы рулетки</h1>
      {CATALOG.map((table) => {
        const live = rooms.find((r) => r.room_id === table.id);
        return (
          <article key={table.id} className="op-table-row">
            <strong>{table.name}</strong>
            <div>
              min {table.min} PLAY · max {table.max} PLAY · {live?.seats_taken ?? 0}/{table.seats} ·{" "}
              {table.live ? live?.status_label || "Идет прием ставок" : "Скоро"}
            </div>
            {table.live ? (
              <Link className="op-cta" to={`/casino/roulette/${table.id}`}>
                ENTER
              </Link>
            ) : (
              <button className="op-ghost" type="button" disabled>
                Скоро
              </button>
            )}
          </article>
        );
      })}
    </div>
  );
}
