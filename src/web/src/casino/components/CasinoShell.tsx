import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuthStore } from "@/auth/authStore";
import { formatPlayBalance } from "../currency";
import { useCasinoWallet } from "../useCasinoSession";
import { grantDemoChips } from "../casinoApi";
import { CasinoHistoryDrawer } from "../CasinoHistoryDrawer";
import { casinoSound } from "../casinoSound";
import { useEffect, useState } from "react";
import { RoomTransition } from "../transitions/RoomTransition";
import { useRoomTransition } from "../transitions/useRoomTransition";
import "../odessa.css";
import "../assets/world.css";

const NAV = [
  { to: "/enterprise-city?building=casino", label: "Город", end: false },
  { to: "/casino", label: "Казино", end: true },
  { to: "/casino/floor", label: "Зал" },
  { to: "/casino/rooms/roulette", label: "Рулетка" },
  { to: "/casino/rooms/blackjack", label: "Blackjack" },
  { to: "/casino/rooms/slots", label: "Автоматы" },
];

export function CasinoShell() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const wallet = useCasinoWallet();
  const { phase } = useRoomTransition();
  const [historyOpen, setHistoryOpen] = useState(false);
  const [muted, setMuted] = useState(() => casinoSound.muted);
  const [grantBusy, setGrantBusy] = useState(false);
  const initial = (user?.name || user?.email || "P").slice(0, 1).toUpperCase();

  useEffect(() => {
    casinoSound.setMuted(muted);
  }, [muted]);

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
    <div className="op-root op-world" data-testid="casino-shell">
      <RoomTransition phase={phase} />
      <header className="op-header">
        <NavLink to="/casino" className="op-logo" aria-label="Odessa Prime Casino">
          <strong>ODESSA PRIME</strong>
          <span>CASINO</span>
        </NavLink>
        <nav className="op-nav" aria-label="Казино">
          {NAV.map((item) => (
            <NavLink
              key={item.label}
              to={item.to}
              end={item.end}
              className={({ isActive }) => (isActive ? "is-active" : undefined)}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="op-hud">
          <div className="op-chip-balance" aria-live="polite">
            {wallet.wallet ? formatPlayBalance(wallet.wallet.balance_chips) : "PLAY"}
          </div>
          {wallet.wallet?.demo_grant_available ? (
            <button className="op-grant" type="button" disabled={grantBusy} onClick={() => void grant()}>
              ПОЛУЧИТЬ 5 000 PLAY
            </button>
          ) : null}
          <button className="op-icon-btn" type="button" aria-label={muted ? "Включить звук" : "Выключить звук"} onClick={() => setMuted((m) => !m)}>
            {muted ? "🔇" : "🔊"}
          </button>
          <button className="op-ghost" type="button" onClick={() => setHistoryOpen(true)}>
            История
          </button>
          <button className="op-ghost" type="button" onClick={() => navigate("/enterprise-city?building=casino")}>
            В город
          </button>
          <span className="op-avatar" aria-label={user?.name || "Профиль"}>
            {initial}
          </span>
        </div>
      </header>
      <main className="op-main">
        <Outlet context={{ wallet }} />
      </main>
      <nav className="op-bottom" aria-label="Мобильная навигация казино">
        <NavLink to="/casino" end>
          Лобби
        </NavLink>
        <NavLink to="/casino/floor">Зал</NavLink>
        <NavLink to="/casino/rooms/roulette">Рулетка</NavLink>
        <NavLink to="/casino/rooms/blackjack">BJ</NavLink>
        <NavLink to="/casino/rooms/slots">Слоты</NavLink>
      </nav>
      {historyOpen ? (
        <CasinoHistoryDrawer items={wallet.ledger} onClose={() => setHistoryOpen(false)} loading={wallet.loading} />
      ) : null}
    </div>
  );
}
