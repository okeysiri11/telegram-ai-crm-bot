import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { useNavigate } from "react-router-dom";
import { cabinetAspectRatio, cabinetImageUrl, HALL_BACKGROUND_URL } from "./cabinetAssets";
import { cabinetControls, controlTestId } from "./cabinetControls";
import { cabinetPlayLayout, seatedCrop, type OverlayRect } from "./cabinetPlayGeometry";
import { SlotReels } from "./SlotReels";
import { usePhysicalCabinetControls } from "./usePhysicalCabinetControls";
import { useSlotDemo } from "./useSlotDemo";
import type { SlotGameDefinition } from "./slotTypes";
import "./seatedCabinet.css";

type Props = { def: SlotGameDefinition };
type SeatPhase = "arriving" | "seated" | "leaving";

function motionDelay(fullMs: number, reducedMs = 140): number {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return reducedMs;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches ? reducedMs : fullMs;
}

function pct(r: OverlayRect): CSSProperties {
  return {
    left: `${r.leftPct}%`,
    top: `${r.topPct}%`,
    width: `${r.widthPct}%`,
    height: `${r.heightPct}%`,
    borderRadius: r.borderRadius != null ? `${r.borderRadius}px` : undefined,
  };
}

export function SeatedSlotCabinet({ def }: Props) {
  const navigate = useNavigate();
  const demo = useSlotDemo(def);
  const controls = usePhysicalCabinetControls(def, demo);
  const [phase, setPhase] = useState<SeatPhase>(() => (motionDelay(640, 0) === 0 ? "seated" : "arriving"));
  const layout = useMemo(() => cabinetPlayLayout(def), [def]);
  const hits = useMemo(() => cabinetControls(def), [def]);
  const crop = useMemo(() => seatedCrop(def), [def]);
  const cabinetImg = cabinetImageUrl(def);
  const settled = Boolean(demo.result && !demo.spinning);

  useEffect(() => {
    if (phase !== "arriving") return undefined;
    const id = window.setTimeout(() => setPhase("seated"), motionDelay(640, 0));
    return () => window.clearTimeout(id);
  }, [phase]);

  function goBack() {
    const wait = motionDelay(560, 0);
    if (!wait) {
      navigate("/casino/slots");
      return;
    }
    setPhase("leaving");
    window.setTimeout(() => navigate("/casino/slots"), wait);
  }

  function onControl(action: (typeof hits)[number]["action"], hit: (typeof hits)[number]) {
    if (action === "spin") {
      controls.play();
      return;
    }
    if (action === "bet" && hit.bet != null) {
      controls.setBet(hit.bet);
      return;
    }
    if (action === "bet-step" && hit.step) {
      controls.stepBet(hit.step);
      return;
    }
    if (action === "auto") {
      controls.setAuto((v) => !v);
      return;
    }
    if (action === "cashout") {
      controls.cashOut();
      return;
    }
    if (action === "service") {
      controls.setServiceOpen((v) => !v);
      return;
    }
    if (action === "insert-card") {
      controls.insertCard();
      return;
    }
    if (action === "insert-bill") {
      controls.insertBill();
    }
  }

  return (
    <section
      className={`op-slot-focus op-seated theme-${def.theme}${demo.spinning ? " is-spinning" : ""} is-${phase}`}
      data-testid="slot-game-screen"
      data-machine={def.id}
      data-phase={demo.spinning ? "spinning" : settled ? "result" : "idle"}
      data-seated="true"
      data-pov="first-person"
      data-card={controls.cardInserted ? "in" : "out"}
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
        <div className="op-seated-hud-right">
          <span className="op-demo-badge" data-testid="slot-demo-badge">
            Демо-режим
          </span>
          <button
            type="button"
            className="op-seated-back"
            data-testid="slot-history-toggle"
            onClick={() => controls.setHistoryOpen((v) => !v)}
          >
            История
          </button>
        </div>
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
              <div className="op-seated-meters" data-testid="slot-lower-screen">
                <span>
                  БАЛАНС <b data-testid="slot-demo-balance">{demo.balance}</b>
                </span>
                <span>
                  СТАВКА <b data-testid="slot-demo-bet">{controls.bet}</b>
                </span>
                <span>
                  ВЫИГРЫШ <b data-testid="slot-demo-win">{settled ? demo.result?.win || 0 : 0}</b>
                </span>
              </div>
              <div className="op-seated-glass" aria-hidden />
            </div>
            {controls.historyOpen ? (
              <ol className="op-seated-history" data-testid="slot-history" style={pct(layout.history)}>
                {demo.history.length === 0 ? <li>Пока нет спинов</li> : null}
                {demo.history.map((item) => (
                  <li key={`${item.ts}-${item.machineId}-${item.bet}`}>
                    {item.game} · ставка {item.bet} · выигрыш {item.win}
                  </li>
                ))}
              </ol>
            ) : null}
            {controls.serviceOpen ? (
              <aside className="op-seated-service" data-testid="slot-service-panel" style={pct(layout.history)}>
                Сервисный режим · только демо. Повторите SERVICE чтобы закрыть.
              </aside>
            ) : null}
            <div className="op-seated-hits" data-testid="slot-controls-seated">
              {hits.map((hit) => {
                const on =
                  (hit.action === "bet" && hit.bet === controls.bet) ||
                  (hit.action === "auto" && controls.auto) ||
                  (hit.action === "service" && controls.serviceOpen) ||
                  (hit.action === "insert-card" && controls.cardInserted);
                const busy = demo.spinning && (hit.action === "spin" || hit.action === "bet" || hit.action === "bet-step" || hit.action === "cashout");
                return (
                  <button
                    key={hit.id}
                    type="button"
                    className={`op-phys-hit${on ? " is-on" : ""}${hit.action === "spin" && demo.spinning ? " is-lit" : ""}`}
                    data-shape={hit.shape}
                    data-source={hit.painted ? "painted" : "nearest-deck"}
                    data-testid={controlTestId(hit)}
                    style={pct(hit)}
                    disabled={busy}
                    aria-label={hit.ariaLabel}
                    aria-pressed={hit.action === "auto" || hit.action === "service" ? on : undefined}
                    onClick={() => onControl(hit.action, hit)}
                  >
                    <span className="sr-only">{hit.ariaLabel}</span>
                  </button>
                );
              })}
            </div>
            {demo.error || controls.notice ? (
              <p className="op-seated-error" role="status">
                {demo.error || controls.notice}
              </p>
            ) : null}
          </article>
        </div>
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
