import { useMemo, useState, type CSSProperties } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { casinoSound } from "../../casinoSound";
import { getSlotDefinition } from "./slotCatalog";
import { SlotReels } from "./SlotReels";
import { useSlotDemo } from "./useSlotDemo";
import "./slotsHall.css";

export function SlotGameScreen() {
  const { machineId = "" } = useParams();
  const def = useMemo(() => getSlotDefinition(machineId), [machineId]);
  if (!def) return <Navigate to="/casino/slots" replace />;
  return <SlotCabinetPlay def={def} />;
}

function SlotCabinetPlay({ def }: { def: NonNullable<ReturnType<typeof getSlotDefinition>> }) {
  const demo = useSlotDemo(def);
  const [bet, setBet] = useState(def.betSteps[0] || 10);
  const [historyOpen, setHistoryOpen] = useState(false);

  function play() {
    if (demo.spinning) return;
    casinoSound.spin();
    const next = demo.spin(bet);
    if (!next) return;
    window.setTimeout(() => {
      casinoSound.slotStop();
      if (next.win > 0) casinoSound.win();
    }, 1100);
  }

  const settled = Boolean(demo.result && !demo.spinning);

  return (
    <section
      className={`op-slot-focus theme-${def.theme}`}
      data-testid="slot-game-screen"
      data-machine={def.id}
      data-phase={demo.spinning ? "spinning" : settled ? "result" : "idle"}
      style={{ "--cab-accent": def.accent, "--cab-accent-2": def.accent2 } as CSSProperties}
      aria-label={def.title}
    >
      <div className="op-slot-focus-back">
        <Link className="op-ghost" to="/casino/slots" data-testid="slot-back-room">
          Назад к автоматам
        </Link>
        <span className="op-demo-badge" data-testid="slot-demo-badge">
          Демо-режим
        </span>
      </div>
      <div className="op-slot-focus-cabinet">
        <div className="op-hall-cabinet-top">
          <span className="op-hall-marquee">{def.title}</span>
        </div>
        <p className="op-hall-provider">{def.subtitle} · {def.provider}</p>
        <SlotReels def={def} grid={demo.result?.grid || []} spinning={demo.spinning} />
        <p className="op-slot-focus-status" data-testid="slot-result-line">
          {demo.spinning
            ? "Барабаны вращаются…"
            : settled
              ? `${demo.result?.outcome === "win" ? "Выигрыш" : "Без выигрыша"} · ${demo.result?.win || 0}`
              : "Демо-режим · результат из игрового движка"}
        </p>
        {demo.error ? (
          <p className="op-status" role="alert">
            {demo.error}
          </p>
        ) : null}
        <div className="op-slot-focus-panel">
          <dl className="op-slot-meters">
            <div>
              <dt>Баланс</dt>
              <dd data-testid="slot-demo-balance">{demo.balance}</dd>
            </div>
            <div>
              <dt>Ставка</dt>
              <dd data-testid="slot-demo-bet">{bet}</dd>
            </div>
            <div>
              <dt>Выигрыш</dt>
              <dd data-testid="slot-demo-win">{settled ? demo.result?.win || 0 : 0}</dd>
            </div>
          </dl>
          <div className="op-slot-focus-actions">
            <button type="button" className="op-ghost" disabled={demo.spinning} onClick={() => setBet((n) => def.betSteps[Math.max(0, def.betSteps.indexOf(n) - 1)] || n)}>
              −
            </button>
            {def.betSteps.map((n) => (
              <button key={n} type="button" className={`op-ghost${bet === n ? " is-on" : ""}`} disabled={demo.spinning} onClick={() => setBet(n)}>
                {n}
              </button>
            ))}
            <button type="button" className="op-ghost" disabled={demo.spinning} onClick={() => setBet((n) => def.betSteps[Math.min(def.betSteps.length - 1, def.betSteps.indexOf(n) + 1)] || n)}>
              +
            </button>
            <button className="op-cta" type="button" disabled={demo.spinning} data-testid="slot-spin" onClick={play}>
              Крутить
            </button>
            <button className="op-ghost" type="button" disabled>
              Авто
            </button>
          </div>
        </div>
        <button type="button" className="op-ghost op-slot-history-toggle" data-testid="slot-history-toggle" onClick={() => setHistoryOpen((v) => !v)}>
          История
        </button>
        {historyOpen ? (
          <ol className="op-slot-history" data-testid="slot-history">
            {demo.history.length === 0 ? <li>Пока нет спинов</li> : null}
            {demo.history.map((item) => (
              <li key={`${item.ts}-${item.machineId}-${item.bet}`}>
                {item.game} · ставка {item.bet} · выигрыш {item.win}
              </li>
            ))}
          </ol>
        ) : null}
      </div>
    </section>
  );
}

export default SlotGameScreen;
