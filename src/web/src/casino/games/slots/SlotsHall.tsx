import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CASINO_ROUTES } from "../../state/casinoRoutes";
import { PhysicalSlotMachine } from "./PhysicalSlotMachine";
import { filterSlotCatalog, SLOT_CATALOG, SLOT_FILTERS } from "./slotCatalog";
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
  const [selected, setSelected] = useState<string | null>(null);

  const items = useMemo(() => filterSlotCatalog(query, filter), [query, filter]);

  return (
    <section className="op-slots-hall" data-testid="slots-room" aria-label="Зал автоматов">
      <div className="op-slots-env" aria-hidden>
        <div className="op-slots-ceiling" />
        <div className="op-slots-chandelier" />
        <div className="op-slots-columns" />
        <div className="op-slots-haze" />
        <div className="op-slots-depth" />
        <div className="op-slots-floor" />
      </div>
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
        <h1 className="op-slots-title">SLOTS</h1>
        <div className="op-slots-tools">
          <input
            className="op-slots-search"
            data-testid="slots-search"
            placeholder="Поиск"
            aria-label="Поиск игры"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className="op-slots-filters" data-testid="slots-filters">
            {SLOT_FILTERS.map((item) => (
              <button
                key={item.id}
                type="button"
                className={filter === item.id ? "is-on" : undefined}
                onClick={() => setFilter(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </header>
      <div className={`op-slots-stage${selected ? " is-choosing" : ""}`} data-selected={selected || undefined}>
        <div className="op-slots-row" data-testid="slots-catalog">
          {items.map((def, index) => (
            <PhysicalSlotMachine
              key={def.id}
              def={def}
              index={index}
              selected={selected === def.id}
              onSelect={(id, href, event) => {
                event.preventDefault();
                setSelected(id);
                window.setTimeout(() => navigate(href), 180);
              }}
            />
          ))}
        </div>
      </div>
      <p className="sr-only">{SLOT_CATALOG.length} автоматов в каталоге</p>
    </section>
  );
}

export default SlotsHall;
