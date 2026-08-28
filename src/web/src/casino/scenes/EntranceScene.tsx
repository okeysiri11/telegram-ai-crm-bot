import { useEffect, useRef, useState, type MouseEvent } from "react";
import { useNavigate, useOutletContext } from "react-router-dom";
import { formatPlayBalance, PLAY_LABEL } from "../currency";
import { useCasinoWallet } from "../useCasinoSession";
import { CASINO_ROUTES } from "../state/casinoRoutes";
import { casinoSound } from "../casinoSound";
import { CasinoFacade } from "../entrance/CasinoFacade";
import { CasinoGamePreviewStrip } from "../entrance/CasinoGamePreviewStrip";
import { CasinoSoonModal } from "../components/CasinoSoonModal";
import { ENTER_CASINO_MS, ENTRANCE_PRESENTATION } from "../entrance/presentation";

function prefersReducedMotion() {
  return typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
}

export function EntranceScene() {
  const outlet = useOutletContext<{ wallet?: ReturnType<typeof useCasinoWallet> }>();
  const wallet =
    outlet?.wallet ?? {
      wallet: null,
      ledger: [],
      loading: false,
      error: null,
      refresh: async () => undefined,
      setWallet: () => undefined,
      setLedger: () => undefined,
    };
  const navigate = useNavigate();
  const [entering, setEntering] = useState(false);
  const [soon, setSoon] = useState<string | null>(null);
  const reduced = prefersReducedMotion();
  const timer = useRef<number | null>(null);
  const raf = useRef<number>(0);
  const rootRef = useRef<HTMLElement>(null);

  useEffect(
    () => () => {
      if (timer.current != null) window.clearTimeout(timer.current);
      if (raf.current) window.cancelAnimationFrame(raf.current);
    },
    [],
  );

  function setParallax(x: number, y: number) {
    const el = rootRef.current;
    if (!el) return;
    el.style.setProperty("--px", x.toFixed(3));
    el.style.setProperty("--py", y.toFixed(3));
  }

  function onMove(event: MouseEvent<HTMLElement>) {
    if (reduced || prefersReducedMotion()) return;
    const el = event.currentTarget;
    const rect = el.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width - 0.5) * 2;
    const y = ((event.clientY - rect.top) / rect.height - 0.5) * 2;
    if (raf.current) return;
    raf.current = window.requestAnimationFrame(() => {
      raf.current = 0;
      setParallax(x, y);
    });
  }

  function onLeave() {
    if (raf.current) {
      window.cancelAnimationFrame(raf.current);
      raf.current = 0;
    }
    setParallax(0, 0);
  }

  function enterCasino() {
    casinoSound.door();
    if (reduced || prefersReducedMotion()) {
      navigate(CASINO_ROUTES.lobbyAlias);
      return;
    }
    setEntering(true);
    if (timer.current != null) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => {
      navigate(CASINO_ROUTES.lobbyAlias);
    }, ENTER_CASINO_MS);
  }

  const balance = wallet.wallet ? formatPlayBalance(wallet.wallet.balance_chips) : "—";

  return (
    <section
      ref={rootRef}
      className={`op-entrance op-cinematic op-facade-hero${entering ? " is-entering" : ""}`}
      aria-label="Вход Odessa Prime"
      data-testid="casino-entrance"
      data-entering={entering ? "true" : "false"}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
    >
      <CasinoFacade entering={entering} />
      <div className="op-hero op-hero-facade" data-testid="casino-hero">
        <div className="op-hero-copy">
          <p className="op-kicker op-sign-shimmer">ODESSA PRIME</p>
          <h1 className="op-title">
            ODESSA PRIME
            <span>CASINO</span>
          </h1>
          <p className="op-sub">Добро пожаловать в мир азарта и роскоши</p>
          <p className="op-demo-label">ИГРАЙТЕ НА DEMO CHIPS</p>
          <button
            className="op-enter-cta"
            type="button"
            data-testid="casino-enter-cta"
            disabled={entering}
            onMouseEnter={() => casinoSound.hover()}
            onClick={enterCasino}
          >
            ВОЙТИ В КАЗИНО
          </button>
          <div className="op-status-row" data-testid="casino-status-panels">
            <article className="op-glass-panel" data-demo="presentation">
              <span>LIVE ИГРОКИ</span>
              <b>{ENTRANCE_PRESENTATION.livePlayers}</b>
              <small>
                <i className="op-online-dot" aria-hidden /> онлайн
              </small>
            </article>
            <article className="op-glass-panel">
              <span>ДЕМО БАЛАНС</span>
              <b>{balance}</b>
              <small>{PLAY_LABEL}</small>
            </article>
            <article className="op-glass-panel" data-demo="presentation">
              <span>JACKPOT</span>
              <b>{ENTRANCE_PRESENTATION.jackpotPlay.toLocaleString("ru-RU")}</b>
              <small>{PLAY_LABEL}</small>
            </article>
          </div>
        </div>
      </div>
      <CasinoGamePreviewStrip onSoon={setSoon} />
      {entering ? <div className="op-enter-veil" data-testid="casino-enter-veil" aria-hidden /> : null}
      {soon ? <CasinoSoonModal title={soon} onClose={() => setSoon(null)} /> : null}
    </section>
  );
}
