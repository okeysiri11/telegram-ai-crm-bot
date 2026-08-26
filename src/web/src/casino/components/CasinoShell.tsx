import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuthStore } from "@/auth/authStore";
import { formatPlayBalance } from "../currency";
import { useCasinoWallet } from "../useCasinoSession";
import { grantDemoChips } from "../casinoApi";
import { CasinoHistoryDrawer } from "../CasinoHistoryDrawer";
import { casinoSound } from "../casinoSound";
import { useEffect, useState } from "react";
import { RoomTransitionHost } from "../transitions/RoomTransition";
import { RoomTransitionProvider } from "../transitions/RoomTransitionProvider";
import { usePerformanceTier } from "../hooks/usePerformanceTier";
import { AmbientLayer } from "../ambient/AmbientLayer";
import { bindCasinoRoomAudio } from "../audio/casinoAudio";
import { CasinoGuestProvider } from "./CasinoGuestModal";
import "../odessa.css";
import "../assets/world.css";
import "../assets/entrance.css";
import "../ambient/ambient.css";
import "../assets/live.css";
import "../assets/interact.css";
import "../assets/rooms-visual.css";
import "../assets/lobby.css";

const GLOBAL_NAV = [
  { to: "/enterprise-city?building=casino", label: "ГОРОД", id: "city" },
  { to: "/casino", label: "КАЗИНО", id: "casino", end: true },
  { to: "/casino/promos", label: "АКЦИИ", id: "promos" },
  { to: "/casino/tournaments", label: "ТУРНИРЫ", id: "tournaments" },
  { to: "/casino/support", label: "ПОДДЕРЖКА", id: "support" },
];

const ROOM_NAV = [
  { to: "/casino/lobby", label: "ЛОББИ", id: "lobby" },
  { to: "/casino/games", label: "ИГРОВЫЕ ЗАЛЫ", id: "halls" },
  { to: "/casino/vip", label: "VIP", id: "vip" },
  { to: "/casino/bar", label: "БАР", id: "bar" },
  { to: "/casino/restaurant", label: "РЕСТОРАН", id: "restaurant" },
];

export function casinoNavActive(path: string, id: string, to: string, end?: boolean): boolean {
  if (id === "casino") return path === "/casino" || path === "/casino/";
  if (id === "lobby") {
    return path === "/casino/lobby" || path === "/casino/floor" || path === "/casino/map";
  }
  if (id === "halls") {
    return (
      path.startsWith("/casino/games") ||
      path.startsWith("/casino/halls") ||
      path.includes("/roulette") ||
      path.includes("blackjack") ||
      path.includes("/slots") ||
      path.includes("poker")
    );
  }
  if (end) return path === to || path === `${to}/`;
  return path === to || path.startsWith(`${to}/`) || path.startsWith(`${to}?`);
}

export function CasinoShell() {
  return (
    <CasinoGuestProvider>
      <RoomTransitionProvider>
        <CasinoShellFrame />
      </RoomTransitionProvider>
    </CasinoGuestProvider>
  );
}

function CasinoShellFrame() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const wallet = useCasinoWallet();
  const tier = usePerformanceTier();
  const [historyOpen, setHistoryOpen] = useState(false);
  const [muted, setMuted] = useState(() => casinoSound.muted);
  const [grantBusy, setGrantBusy] = useState(false);
  const initial = (user?.name || user?.email || "P").slice(0, 1).toUpperCase();

  useEffect(() => {
    casinoSound.setMuted(muted);
  }, [muted]);

  useEffect(() => {
    bindCasinoRoomAudio(location.pathname);
  }, [location.pathname]);

  async function grant() {
    setGrantBusy(true);
    try {
      const next = await grantDemoChips();
      wallet.setWallet(next);
      casinoSound.win();
      await wallet.refresh();
    } catch {
      /* cooldown / cap */
    } finally {
      setGrantBusy(false);
    }
  }

  return (
    <div className="op-root op-world" data-testid="casino-shell" data-art="odessa-prime" data-tier={tier}>
      <a className="op-skip" href="#op-main">
        К содержимому
      </a>
      <div className="op-uw-wings" aria-hidden />
      <AmbientLayer tier={tier} />
      <RoomTransitionHost />
      <header className="op-header">
        <NavLink to="/casino" className="op-logo" aria-label="Odessa Prime Casino">
          <strong>ODESSA PRIME</strong>
          <span>CASINO</span>
        </NavLink>
        <div className="op-header-stack">
          <nav className="op-nav" aria-label="Казино">
            {GLOBAL_NAV.map((item) => (
              <NavLink
                key={item.id}
                to={item.to}
                end={item.end}
                className={() => (casinoNavActive(location.pathname, item.id, item.to, item.end) ? "is-active" : undefined)}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <nav className="op-nav op-nav-rooms" aria-label="Залы">
            {ROOM_NAV.map((item) => (
              <NavLink
                key={item.id}
                to={item.to}
                className={() => (casinoNavActive(location.pathname, item.id, item.to) ? "is-active" : undefined)}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="op-hud">
          <div className="op-chip-balance" aria-live="polite">
            {wallet.wallet ? formatPlayBalance(wallet.wallet.balance_chips) : "PLAY"}
          </div>
          {wallet.wallet?.demo_grant_available ? (
            <button className="op-grant" type="button" disabled={grantBusy} onClick={() => void grant()}>
              ПОЛУЧИТЬ 5 000 PLAY
            </button>
          ) : null}
          <button
            className="op-icon-btn"
            type="button"
            data-testid="casino-sound-toggle"
            aria-label={muted ? "Включить звук" : "Выключить звук"}
            aria-pressed={!muted}
            onClick={() => setMuted((m) => !m)}
          >
            {muted ? "🔇" : "🔊"}
          </button>
          <button className="op-ghost" type="button" onClick={() => setHistoryOpen(true)}>
            История
          </button>
          <span className="op-avatar" aria-label={user?.name || "Профиль"}>
            {initial}
          </span>
          <button
            className="op-ghost op-to-city"
            type="button"
            data-testid="casino-to-city"
            onClick={() => navigate("/enterprise-city?building=casino")}
          >
            В ГОРОД
          </button>
        </div>
      </header>
      <main className="op-main" id="op-main">
        <Outlet context={{ wallet }} />
      </main>
      <nav className="op-bottom" aria-label="Мобильная навигация казино">
        <NavLink to="/casino" end>
          Казино
        </NavLink>
        <NavLink to="/casino/lobby">Лобби</NavLink>
        <NavLink to="/casino/games">Залы</NavLink>
        <NavLink to="/casino/vip">VIP</NavLink>
        <NavLink to="/enterprise-city?building=casino">Город</NavLink>
      </nav>
      {historyOpen ? (
        <CasinoHistoryDrawer items={wallet.ledger} onClose={() => setHistoryOpen(false)} loading={wallet.loading} />
      ) : null}
    </div>
  );
}
