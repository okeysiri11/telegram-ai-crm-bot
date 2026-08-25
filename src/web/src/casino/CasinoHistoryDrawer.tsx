import { formatLedgerDelta, formatPlayBalance, formatTimestamp } from "./currency";
import type { CasinoLedgerEntry } from "./types";
import { useMemo, useState } from "react";

const FILTERS = [
  { id: "all", label: "ВСЕ" },
  { id: "wager", label: "СТАВКИ" },
  { id: "payout", label: "ВЫИГРЫШИ" },
  { id: "demo_grant", label: "ДЕМО-ФИШКИ" },
] as const;

export function CasinoHistoryDrawer({
  items,
  loading,
  onClose,
}: {
  items: CasinoLedgerEntry[];
  loading: boolean;
  onClose: () => void;
}) {
  const [filter, setFilter] = useState<(typeof FILTERS)[number]["id"]>("all");
  const rows = useMemo(() => {
    if (filter === "all") return items;
    if (filter === "payout") return items.filter((r) => r.entry_type === "payout" || r.win_loss === "win");
    return items.filter((r) => r.entry_type === filter);
  }, [filter, items]);

  return (
    <aside className="op-drawer" role="dialog" aria-label="История PLAY">
      <div className="op-toolbar">
        <strong>История</strong>
        <button className="op-ghost" type="button" onClick={onClose}>
          Закрыть
        </button>
      </div>
      <div className="op-toggle" role="tablist">
        {FILTERS.map((f) => (
          <button key={f.id} type="button" className={filter === f.id ? "is-on" : undefined} onClick={() => setFilter(f.id)}>
            {f.label}
          </button>
        ))}
      </div>
      {loading && !items.length ? <p className="op-status">Загрузка…</p> : null}
      {!loading && !rows.length ? <p className="op-status">Пока нет операций PLAY.</p> : null}
      <table className="op-history">
        <thead>
          <tr>
            <th>Игра</th>
            <th>Время</th>
            <th>Ставка</th>
            <th>Δ PLAY</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.entry_id}>
              <td>{row.reference_type === "blackjack" ? "Blackjack" : row.reference_type === "slots" ? "Odessa Gold" : "Рулетка"}</td>
              <td>{formatTimestamp(row.created_ts)}</td>
              <td>{row.wager != null ? formatPlayBalance(row.wager) : row.operation}</td>
              <td className={row.balance_delta >= 0 ? "op-win" : "op-loss"}>{formatLedgerDelta(row.balance_delta)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </aside>
  );
}
