import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuthStore } from "@/auth/authStore";
import { formatPlayBalance } from "./currency";
import { useCasinoWallet } from "./useCasinoSession";
import { grantDemoChips } from "./casinoApi";
import { CasinoHistoryDrawer } from "./CasinoHistoryDrawer";
import { casinoSound } from "./casinoSound";
import { useEffect, useState } from "react";
import "./odessa.css";

const NAV = [
  { to: "/enterprise-city?building=casino", label: "Город", end: false, external: true },
  { to: "/casino", label: "Казино", end: true },
  { to: "/casino/games", label: "Акции" },
  { to: "/casino/games", label: "VIP", hash: "vip" },
  { to: "/casino/games", label: "Турниры", hash: "tournaments" },
];

export function CasinoShell() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const wallet = useCasinoWallet();
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
      /* cooldown / cap — keep current HUD */
    } finally {
      setGrantBusy(false);
    }
  }

  return (
    <div className="op-root">
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
              className={({ isActive }) => (isActive && item.to === "/casino" ? "is-active" : undefined)}
            >
              {item.label}
            </NavLink>
          ))}
          <button type="button" onClick={() => setHistoryOpen(true)}>
            Поддержка
          </button>
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
        <NavLink to="/casino" end className={({ isActive }) => (isActive ? "is-active" : undefined)}>
          Лобби
        </NavLink>
        <NavLink to="/casino/floor" className={({ isActive }) => (isActive ? "is-active" : undefined)}>
          Зал
        </NavLink>
        <NavLink to="/casino/roulette" className={({ isActive }) => (isActive ? "is-active" : undefined)}>
          Столы
        </NavLink>
        <button type="button" onClick={() => setHistoryOpen(true)} style={{ flex: 1, background: "transparent", border: 0, color: "inherit" }}>
          История
        </button>
        <NavLink to="/casino/games">Профиль</NavLink>
      </nav>
      {historyOpen ? (
        <CasinoHistoryDrawer
          items={wallet.ledger}
          onClose={() => setHistoryOpen(false)}
          loading={wallet.loading}
        />
      ) : null}
    </div>
  );
}
