import { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

const ZONES = [
  { id: "lobby", label: "ЛОББИ", soon: false, route: "/casino", x: "8%", y: "8%", w: "28%", h: "22%" },
  { id: "roulette", label: "РУЛЕТКА", soon: false, route: "/casino/roulette", x: "40%", y: "18%", w: "32%", h: "28%" },
  { id: "blackjack", label: "BLACKJACK", soon: true, route: "/casino/floor?zone=blackjack", x: "74%", y: "12%", w: "20%", h: "24%" },
  { id: "poker", label: "ПОКЕР", soon: true, route: "/casino/floor?zone=poker", x: "10%", y: "38%", w: "24%", h: "26%" },
  { id: "slots", label: "АВТОМАТЫ", soon: true, route: "/casino/floor?zone=slots", x: "38%", y: "52%", w: "28%", h: "20%" },
  { id: "vip", label: "VIP ЗОНА", soon: true, route: "/casino/floor?zone=vip", x: "70%", y: "42%", w: "24%", h: "22%" },
  { id: "bar", label: "БАР", soon: true, route: "/casino/floor?zone=bar", x: "8%", y: "72%", w: "30%", h: "20%" },
  { id: "restaurant", label: "РЕСТОРАН", soon: true, route: "/casino/floor?zone=restaurant", x: "48%", y: "74%", w: "44%", h: "18%" },
] as const;

export function CasinoFloorPage() {
  const [mode, setMode] = useState<"hall" | "map">("hall");
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const here = params.get("zone") || "lobby";

  const zones = useMemo(() => ZONES, []);

  function open(zone: (typeof ZONES)[number]) {
    if (zone.id === "roulette") {
      navigate("/casino/roulette");
      return;
    }
    if (zone.id === "lobby") {
      navigate("/casino");
      return;
    }
    navigate(`/casino/floor?zone=${zone.id}`);
  }

  return (
    <div className="op-floor">
      <div className="op-toolbar">
        <h1 className="op-kicker">Зал Odessa Prime</h1>
        <div className="op-toggle" role="group" aria-label="Вид зала">
          <button type="button" className={mode === "hall" ? "is-on" : undefined} onClick={() => setMode("hall")}>
            ЗАЛ
          </button>
          <button type="button" className={mode === "map" ? "is-on" : undefined} onClick={() => setMode("map")}>
            КАРТА
          </button>
        </div>
      </div>
      {mode === "hall" ? (
        <div className="op-hall" aria-label="Игровой зал">
          {zones.map((zone) => (
            <button
              key={zone.id}
              type="button"
              className={`op-zone${zone.soon ? " is-soon" : ""}${here === zone.id ? " is-on" : ""}`}
              style={{ left: zone.x, top: zone.y, width: zone.w, height: zone.h }}
              onClick={() => open(zone)}
            >
              <small>{zone.soon ? "СКОРО" : "LIVE"}</small>
              {zone.label}
            </button>
          ))}
        </div>
      ) : (
        <div className="op-map" aria-label="Карта казино">
          {zones.map((zone) => (
            <button
              key={zone.id}
              type="button"
              className={`op-map-cell${here === zone.id ? " is-here" : ""}`}
              onClick={() => open(zone)}
            >
              <small className="op-kicker">{zone.soon ? "СКОРО" : "OPEN"}</small>
              <div>{zone.label}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
