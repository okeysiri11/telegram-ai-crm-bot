import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { Link } from "react-router-dom";
import { casinoSound } from "../../casinoSound";
import { cabinetAspectRatio, cabinetImageUrl, HALL_BACKGROUND_URL } from "./cabinetAssets";
import { cabinetPlayLayout } from "./cabinetPlayGeometry";
import { SlotReels } from "./SlotReels";
import { useSlotDemo } from "./useSlotDemo";
import type { SlotGameDefinition } from "./slotTypes";
import "./seatedCabinet.css";

type Props = { def: SlotGameDefinition };

export function SeatedSlotCabinet({ def }: Props) {
  const demo = useSlotDemo(def);
  const [bet, setBet] = useState(def.betSteps[0] || 10);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [auto, setAuto] = useState(false);
  const layout = useMemo(() => cabinetPlayLayout(def), [def]);
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
    if (!auto || demo.spinning) return undefined;
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
  }, [auto, bet, demo.spinning, demo.spin]);

  function stepBet(dir: -1 | 1) {
    const i = def.betSteps.indexOf(bet);
    const next = def.betSteps[Math.max(0, Math.min(def.betSteps.length - 1, i + dir))];
    if (next != null) setBet(next);
  }

  const pct = (r: { leftPct: number; topPct: number; widthPct: number; heightPct: number; borderRadius?: number }): CSSProperties => ({
    left: `${r.leftPct}%`,
    top: `${r.topPct}%`,
    width: `${r.widthPct}%`,
    height: `${r.heightPct}%`,
    borderRadius: r.borderRadius != null ? `${r.borderRadius}px` : undefined,
  });

  return (
    <section
      className={`op-slot-focus op-seated theme-${def.theme}${demo.spinning ? " is-spinning" : ""}`}
      data-testid="slot-game-screen"
      data-machine={def.id}
      data-phase={demo.spinning ? "spinning" : settled ? "result" : "idle"}
      data-seated="true"
      style={{ "--cab-accent": def.accent, "--cab-accent-2": def.accent2 } as CSSProperties}
      aria-label={def.title}
    >
      <div className="op-seated-env" aria-hidden>
        <img className="op-seated-env-bg" src={HALL_BACKGROUND_URL} alt="" />
        <div className="op-seated-env-glow" />
      </div>
      <header className="op-seated-hud">
        <Link className="op-seated-back" to="/casino/slots" data-testid="slot-back-room">
          ← Назад к автоматам
        </Link>
        <span className="op-seated-title">{def.title}</span>
        <div className="op-seated-hud-right">
          <span className="op-demo-badge" data-testid="slot-demo-badge">
            Демо
          </span>
          <button type="button" className="op-seated-text-btn" data-testid="slot-history-toggle" onClick={() => setHistoryOpen((v) => !v)}>
            История
          </button>
        </div>
      </header>
      {historyOpen ? (
        <ol className="op-slot-history op-seated-history" data-testid="slot-history">
          {demo.history.length === 0 ? <li>Пока нет спинов</li> : null}
          {demo.history.map((item) => (
            <li key={`${item.ts}-${item.machineId}-${item.bet}`}>
              {item.game} · ставка {item.bet} · выигрыш {item.win}
            </li>
          ))}
        </ol>
      ) : null}
      <article
        className={`op-seated-cabinet variant-${def.cabinetVariant}`}
        data-testid="seated-cabinet"
        style={{ aspectRatio: cabinetAspectRatio(def) }}
      >
        <img
          className="op-seated-cabinet-img"
          src={cabinetImg}
          alt=""
          data-testid={`slot-seated-asset-${def.id}`}
        />
        <div className="op-seated-screen" data-testid="slot-preview-seated" style={{ ...pct(layout.screen), overflow: "hidden" }}>
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
        <div className="op-seated-deck" style={pct(layout.deck)} data-testid="slot-controls-seated">
          <button type="button" data-testid="slot-bet-minus" disabled={demo.spinning} onClick={() => stepBet(-1)}>
            BET −
          </button>
          {def.betSteps.map((n) => (
            <button key={n} type="button" className={bet === n ? "is-on" : undefined} disabled={demo.spinning} onClick={() => setBet(n)}>
              {n}
            </button>
          ))}
          <button type="button" data-testid="slot-bet-plus" disabled={demo.spinning} onClick={() => stepBet(1)}>
            BET +
          </button>
          <button type="button" data-testid="slot-auto" className={auto ? "is-on" : undefined} onClick={() => setAuto((v) => !v)}>
            AUTO
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
      <p className="sr-only" data-testid="slot-result-line">
        {demo.spinning ? "Барабаны вращаются…" : settled ? `${demo.result?.outcome === "win" ? "Выигрыш" : "Без выигрыша"} · ${demo.result?.win || 0}` : "Демо-режим"}
      </p>
    </section>
  );
}
