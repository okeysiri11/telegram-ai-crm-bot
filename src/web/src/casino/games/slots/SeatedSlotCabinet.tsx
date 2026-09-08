import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { useNavigate } from "react-router-dom";
import { casinoSound } from "../../casinoSound";
import { cabinetAspectRatio, cabinetImageUrl, HALL_BACKGROUND_URL } from "./cabinetAssets";
import { cabinetPlayLayout, seatedCrop, type OverlayRect } from "./cabinetPlayGeometry";
import { SlotReels } from "./SlotReels";
import { useSlotDemo } from "./useSlotDemo";
import type { SlotGameDefinition } from "./slotTypes";
import "./seatedCabinet.css";

type Props = { def: SlotGameDefinition };
type SeatPhase = "arriving" | "seated" | "leaving";

function motionDelay(fullMs: number, reducedMs = 140): number {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return reducedMs;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches ? reducedMs : fullMs;
}

function ArmchairForeground() {
  return (
    <div className="op-seated-fg" data-testid="seated-foreground" aria-hidden>
      <div className="op-seated-seat" data-testid="seated-armchair" />
      <svg className="op-seated-arm op-seated-arm-left" viewBox="0 0 420 220" preserveAspectRatio="none">
        <path d="M0 220 L0 92 C40 38 120 18 210 36 C280 50 340 86 420 128 L420 220 Z" fill="#1a120e" />
        <path d="M0 118 C70 58 150 42 230 58 C300 72 360 108 420 148 L420 176 C340 128 260 92 180 86 C100 80 40 108 0 148 Z" fill="#2a1c16" />
        <path d="M18 128 C90 78 170 66 248 82" fill="none" stroke="#c9a45c" strokeWidth="3" opacity="0.55" />
        <circle cx="46" cy="142" r="4" fill="#d4b56a" />
        <circle cx="88" cy="118" r="4" fill="#d4b56a" />
        <circle cx="136" cy="104" r="4" fill="#d4b56a" />
        <circle cx="188" cy="98" r="4" fill="#d4b56a" />
      </svg>
      <svg className="op-seated-arm op-seated-arm-right" viewBox="0 0 420 220" preserveAspectRatio="none">
        <path d="M420 220 L420 92 C380 38 300 18 210 36 C140 50 80 86 0 128 L0 220 Z" fill="#1a120e" />
        <path d="M420 118 C350 58 270 42 190 58 C120 72 60 108 0 148 L0 176 C80 128 160 92 240 86 C320 80 380 108 420 148 Z" fill="#2a1c16" />
        <path d="M402 128 C330 78 250 66 172 82" fill="none" stroke="#c9a45c" strokeWidth="3" opacity="0.55" />
        <circle cx="374" cy="142" r="4" fill="#d4b56a" />
        <circle cx="332" cy="118" r="4" fill="#d4b56a" />
        <circle cx="284" cy="104" r="4" fill="#d4b56a" />
        <circle cx="232" cy="98" r="4" fill="#d4b56a" />
      </svg>
      <div className="op-seated-sidetable" data-testid="seated-ashtray">
        <svg viewBox="0 0 160 150" className="op-seated-ashtray-svg">
          <ellipse cx="80" cy="128" rx="54" ry="10" fill="rgba(0,0,0,0.45)" />
          <rect x="28" y="86" width="104" height="42" rx="6" fill="#3a2a1c" />
          <rect x="28" y="86" width="104" height="10" fill="#c9a45c" opacity="0.35" />
          <ellipse cx="80" cy="78" rx="28" ry="8" fill="#4a4038" />
          <ellipse cx="80" cy="76" rx="22" ry="6" fill="#1a1410" />
          <ellipse cx="80" cy="76" rx="16" ry="4" fill="#2a221c" />
          <rect x="92" y="52" width="5" height="26" rx="2" fill="#d9c4a0" transform="rotate(28 94 65)" />
          <circle cx="108" cy="48" r="3" fill="#ff7a3d" />
          <circle cx="64" cy="74" r="2" fill="#6b5b4f" />
          <circle cx="86" cy="72" r="1.6" fill="#5a4a40" />
          <rect x="46" y="58" width="14" height="22" rx="4" fill="#8a6a3a" opacity="0.8" />
        </svg>
      </div>
    </div>
  );
}

export function SeatedSlotCabinet({ def }: Props) {
  const navigate = useNavigate();
  const demo = useSlotDemo(def);
  const [bet, setBet] = useState(def.betSteps[0] || 10);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [auto, setAuto] = useState(false);
  const [phase, setPhase] = useState<SeatPhase>(() => (motionDelay(640, 0) === 0 ? "seated" : "arriving"));
  const layout = useMemo(() => cabinetPlayLayout(def), [def]);
  const crop = useMemo(() => seatedCrop(def), [def]);
  const cabinetImg = cabinetImageUrl(def);
  const settled = Boolean(demo.result && !demo.spinning);

  const play = () => {
    if (demo.spinning) return;
    casinoSound.spin();
    const next = demo.spin(bet);
    if (!next) return;
    window.setTimeout(() => {
      casinoSound.slotStop();
      if (next.win > 0) casinoSound.win();
    }, 1100);
  };

  useEffect(() => {
    if (phase !== "arriving") return undefined;
    const id = window.setTimeout(() => setPhase("seated"), motionDelay(640, 0));
    return () => window.clearTimeout(id);
  }, [phase]);

  useEffect(() => {
    if (!auto || demo.spinning || phase === "leaving") return undefined;
    const id = window.setTimeout(() => {
      if (demo.spinning) return;
      casinoSound.spin();
      const next = demo.spin(bet);
      if (!next) return;
      window.setTimeout(() => {
        casinoSound.slotStop();
        if (next.win > 0) casinoSound.win();
      }, 1100);
    }, 420);
    return () => window.clearTimeout(id);
  }, [auto, bet, demo.spinning, demo.spin, phase]);

  function stepBet(dir: -1 | 1) {
    const i = def.betSteps.indexOf(bet);
    const next = def.betSteps[Math.max(0, Math.min(def.betSteps.length - 1, i + dir))];
    if (next != null) setBet(next);
  }

  function goBack() {
    const wait = motionDelay(560, 0);
    if (!wait) {
      navigate("/casino/slots");
      return;
    }
    setPhase("leaving");
    window.setTimeout(() => navigate("/casino/slots"), wait);
  }

  const pct = (r: OverlayRect): CSSProperties => ({
    left: `${r.leftPct}%`,
    top: `${r.topPct}%`,
    width: `${r.widthPct}%`,
    height: `${r.heightPct}%`,
    borderRadius: r.borderRadius != null ? `${r.borderRadius}px` : undefined,
  });

  return (
    <section
      className={`op-slot-focus op-seated theme-${def.theme}${demo.spinning ? " is-spinning" : ""} is-${phase}`}
      data-testid="slot-game-screen"
      data-machine={def.id}
      data-phase={demo.spinning ? "spinning" : settled ? "result" : "idle"}
      data-seated="true"
      data-pov="first-person"
      style={{ "--cab-accent": def.accent, "--cab-accent-2": def.accent2 } as CSSProperties}
      aria-label={def.title}
    >
      <div className="op-seated-env" aria-hidden>
        <img className="op-seated-env-bg" src={HALL_BACKGROUND_URL} alt="" />
        <div className="op-seated-bokeh">
          <span />
          <span />
          <span />
          <span />
          <span />
        </div>
        <div className="op-seated-vignette" />
        <div className="op-seated-env-glow" />
      </div>
      <header className="op-seated-hud">
        <button type="button" className="op-seated-back" data-testid="slot-back-room" onClick={goBack}>
          ← Назад к автоматам
        </button>
        <span className="op-seated-title">{def.title}</span>
        <span className="op-demo-badge" data-testid="slot-demo-badge">
          Демо-режим
        </span>
      </header>
      <div className="op-seated-stage">
        <div className="op-seated-rig">
          <article
            className={`op-seated-cabinet variant-${def.cabinetVariant}`}
            data-testid="seated-cabinet"
            style={
              {
                aspectRatio: cabinetAspectRatio(def),
                "--seated-h": `${crop.heightPct}%`,
                "--seated-b": `${crop.bottomPct}%`,
                "--screen-top": `${layout.screen.topPct}%`,
                "--screen-height": `${layout.screen.heightPct}%`,
              } as CSSProperties
            }
          >
            <img
              className="op-seated-cabinet-img"
              src={cabinetImg}
              alt=""
              data-testid={`slot-seated-asset-${def.id}`}
            />
            <div
              className="op-seated-screen"
              data-testid="slot-preview-seated"
              style={{ ...pct(layout.screen), overflow: "hidden" }}
            >
              <div className="op-phys-art" aria-hidden />
              <SlotReels def={def} grid={demo.result?.grid || []} spinning={demo.spinning} />
              <div className="op-seated-glass" aria-hidden />
            </div>
            <div className="op-seated-touch" style={pct(layout.touch)} data-testid="slot-lower-screen">
              <span>ODESSA PRIME</span>
              <span>
                BAL <b data-testid="slot-demo-balance">{demo.balance}</b>
              </span>
              <span>
                BET <b data-testid="slot-demo-bet">{bet}</b>
              </span>
              <span>
                WIN <b data-testid="slot-demo-win">{settled ? demo.result?.win || 0 : 0}</b>
              </span>
            </div>
            {historyOpen ? (
              <ol className="op-seated-history" data-testid="slot-history" style={pct(layout.history)}>
                {demo.history.length === 0 ? <li>Пока нет спинов</li> : null}
                {demo.history.map((item) => (
                  <li key={`${item.ts}-${item.machineId}-${item.bet}`}>
                    {item.game} · ставка {item.bet} · выигрыш {item.win}
                  </li>
                ))}
              </ol>
            ) : null}
            <div className="op-seated-deck" style={pct(layout.deck)} data-testid="slot-controls-seated">
              <button type="button" data-testid="slot-bet-minus" disabled={demo.spinning} onClick={() => stepBet(-1)}>
                BET −
              </button>
              {def.betSteps.map((n) => (
                <button
                  key={n}
                  type="button"
                  className={bet === n ? "is-on" : undefined}
                  disabled={demo.spinning}
                  data-testid={`slot-bet-${n}`}
                  onClick={() => setBet(n)}
                >
                  {n}
                </button>
              ))}
              <button type="button" data-testid="slot-bet-plus" disabled={demo.spinning} onClick={() => stepBet(1)}>
                BET +
              </button>
              <button type="button" data-testid="slot-auto" className={auto ? "is-on" : undefined} onClick={() => setAuto((v) => !v)}>
                AUTO
              </button>
              <button
                type="button"
                data-testid="slot-history-toggle"
                className={historyOpen ? "is-on" : undefined}
                onClick={() => setHistoryOpen((v) => !v)}
              >
                HISTORY
              </button>
            </div>
            <button
              type="button"
              className={`op-seated-spin${demo.spinning ? " is-lit" : ""}`}
              style={pct(layout.spin)}
              disabled={demo.spinning}
              data-testid="slot-spin"
              aria-label="SPIN"
              onClick={play}
            >
              SPIN
            </button>
            {demo.error ? (
              <p className="op-seated-error" role="alert">
                {demo.error}
              </p>
            ) : null}
          </article>
        </div>
        <ArmchairForeground />
      </div>
      <p className="sr-only" data-testid="slot-result-line">
        {demo.spinning
          ? "Барабаны вращаются…"
          : settled
            ? `${demo.result?.outcome === "win" ? "Выигрыш" : "Без выигрыша"} · ${demo.result?.win || 0}`
            : "Демо-режим"}
      </p>
    </section>
  );
}
