import { useEffect, useMemo, useRef } from "react";
import { EUROPEAN_ORDER, WHEEL_SLICE, ballDegreesForNumber, wheelDegreesForNumber, wheelIndexForNumber } from "./wheelMath";

const RED = new Set([1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]);

function wheelBackground(): string {
  return EUROPEAN_ORDER.map((n, i) => {
    const color = n === 0 ? "#0f7a46" : RED.has(n) ? "#8c1c28" : "#141414";
    return `${color} ${i * WHEEL_SLICE}deg ${(i + 1) * WHEEL_SLICE}deg`;
  }).join(",");
}

export function RouletteWheel({
  target,
  spinning,
  onDone,
}: {
  target: number | null;
  spinning: boolean;
  onDone: () => void;
}) {
  const wheelRef = useRef<HTMLDivElement>(null);
  const ballRef = useRef<HTMLDivElement>(null);
  const doneRef = useRef(onDone);
  doneRef.current = onDone;
  const reduced = useMemo(
    () => typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches,
    [],
  );

  useEffect(() => {
    const el = wheelRef.current;
    if (!el || target == null || !spinning) return;
    const extra = reduced ? 0 : 6;
    const deg = wheelDegreesForNumber(target, extra);
    const ballDeg = ballDegreesForNumber(target, extra);
    el.style.transition = "none";
    el.style.transform = "rotate(0deg)";
    void el.offsetWidth;
    const ball = ballRef.current;
    if (ball) {
      ball.style.transition = "none";
      ball.style.transform = "rotate(0deg)";
    }
    const wait = reduced ? 220 : 4900;
    const rest = (37 - Math.max(wheelIndexForNumber(target), 0)) * WHEEL_SLICE;
    const frame = window.requestAnimationFrame(() => {
      el.style.transition = reduced ? "transform 200ms linear" : "transform 4.8s cubic-bezier(0.12, 0.7, 0.2, 1)";
      el.style.transform = `rotate(${deg}deg)`;
      if (ball) {
        ball.style.transition = reduced ? "transform 200ms linear" : "transform 4.2s cubic-bezier(0.05, 0.6, 0.15, 1)";
        ball.style.transform = `rotate(${-ballDeg}deg)`;
      }
    });
    const t = window.setTimeout(() => {
      if (ball) {
        ball.style.transition = "transform 280ms ease-out";
        ball.style.transform = `rotate(${-rest}deg)`;
      }
      doneRef.current();
    }, wait);
    return () => {
      window.cancelAnimationFrame(frame);
      window.clearTimeout(t);
    };
  }, [reduced, spinning, target]);

  return (
    <div className="op-wheel-wrap" data-testid="roulette-wheel">
      <div className="op-wheel-stage">
        <div className="op-wheel-wood" aria-hidden />
        <div ref={ballRef} className="op-ball-ring" data-testid="roulette-ball" aria-hidden>
          <div className="op-ball" />
        </div>
        <div
          ref={wheelRef}
          className={`op-wheel${spinning ? "" : " is-idle"}`}
          style={{ background: `conic-gradient(${wheelBackground()})` }}
          role="img"
          aria-label={target != null ? `Колесо, результат ${target}` : "Колесо рулетки"}
        >
          <span className="op-wheel-hub" />
        </div>
      </div>
    </div>
  );
}

export { EUROPEAN_ORDER } from "./wheelMath";
