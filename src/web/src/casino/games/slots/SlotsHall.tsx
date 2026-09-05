import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CASINO_ROUTES } from "../../state/casinoRoutes";
import { filterSlotCatalog, SLOT_CATALOG, SLOT_FILTERS } from "./slotCatalog";
import { SlotMachineCabinet } from "./SlotMachineCabinet";
import type { SlotFilterId } from "./slotTypes";
import "./slotsHall.css";

const ROOM_LINKS = [
  { id: "slots", label: "SLOTS", to: "/casino/slots" },
  { id: "roulette", label: "ROULETTE", to: "/casino/roulette" },
  { id: "blackjack", label: "BLACKJACK", to: "/casino/blackjack" },
  { id: "poker", label: "POKER", to: "/casino/poker" },
] as const;

export function SlotsHall() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<SlotFilterId>("all");
  const [offset, setOffset] = useState(0);
  const [favorites, setFavorites] = useState<string[]>(() => {
    try {
      return JSON.parse(sessionStorage.getItem("op-slot-favs") || "[]") as string[];
    } catch {
      return [];
    }
  });

  const items = useMemo(() => filterSlotCatalog(query, filter), [query, filter]);
  const visible = items.slice(offset, offset + items.length);

  function toggleFavorite(id: string) {
    setFavorites((prev) => {
      const next = prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id];
      try {
        sessionStorage.setItem("op-slot-favs", JSON.stringify(next));
      } catch {
        /* ignore */
      }
      return next;
    });
  }

  return (
    <section className="op-slots-hall" data-testid="slots-room" aria-label="Зал автоматов">
      <header className="op-slots-subnav">
        <button className="op-ghost" type="button" data-testid="slots-back-hall" onClick={() => navigate(CASINO_ROUTES.lobbyAlias)}>
          ← В ЗАЛ
        </button>
        <nav aria-label="Игровые залы">
          {ROOM_LINKS.map((item) => (
            <Link key={item.id} to={item.to} className={item.id === "slots" ? "is-active" : undefined} data-testid={`slots-nav-${item.id}`}>
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="op-slots-tools">
          <input
            className="op-slots-search"
            data-testid="slots-search"
            placeholder="Поиск игры"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setOffset(0);
            }}
          />
          <div className="op-slots-filters" data-testid="slots-filters">
            {SLOT_FILTERS.map((item) => (
              <button
                key={item.id}
                type="button"
                className={filter === item.id ? "is-on" : undefined}
                onClick={() => {
                  setFilter(item.id);
                  setOffset(0);
                }}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </header>
      <div className="op-slots-heading">
        <p className="op-kicker">SLOTS</p>
        <h1>Выберите автомат</h1>
        <p className="op-status">Демо-режим · PLAY не списывается</p>
      </div>
      <div className="op-slots-stage">
        {items.length > 6 ? (
          <button type="button" className="op-slots-arrow" aria-label="Назад" onClick={() => setOffset((n) => Math.max(0, n - 1))}>
            ‹
          </button>
        ) : null}
        <div className="op-slots-row" data-testid="slots-catalog">
          {visible.map((def) => (
            <SlotMachineCabinet
              key={def.id}
              def={def}
              favorite={favorites.includes(def.id)}
              onFavorite={toggleFavorite}
            />
          ))}
        </div>
        {items.length > 6 ? (
          <button
            type="button"
            className="op-slots-arrow"
            aria-label="Далее"
            onClick={() => setOffset((n) => Math.min(items.length - 1, n + 1))}
          >
            ›
          </button>
        ) : null}
      </div>
      <p className="sr-only">{SLOT_CATALOG.length} автоматов в каталоге</p>
    </section>
  );
}

export default SlotsHall;
