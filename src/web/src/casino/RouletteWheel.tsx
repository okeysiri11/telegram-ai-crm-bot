import { useEffect, useMemo, useRef } from "react";

export const EUROPEAN_ORDER = [
  0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7,
  28, 12, 35, 3, 26,
] as const;

const RED = new Set([1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]);
const SLICE = 360 / 37;

function wheelBackground(): string {
  return EUROPEAN_ORDER.map((n, i) => {
    const color = n === 0 ? "#0f7a46" : RED.has(n) ? "#8c1c28" : "#141414";
    return `${color} ${i * SLICE}deg ${(i + 1) * SLICE}deg`;
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
    const index = EUROPEAN_ORDER.indexOf(target as (typeof EUROPEAN_ORDER)[number]);
    const extra = reduced ? 0 : 6 * 360;
    const deg = extra + (360 - index * SLICE);
    el.style.transition = "none";
    el.style.transform = "rotate(0deg)";
    void el.offsetWidth;
    const ball = ballRef.current;
    if (ball) {
      ball.style.transition = "none";
      ball.style.transform = "rotate(0deg)";
    }
    const wait = reduced ? 220 : 4900;
    const frame = window.requestAnimationFrame(() => {
      el.style.transition = reduced ? "transform 200ms linear" : "transform 4.8s cubic-bezier(0.12, 0.7, 0.2, 1)";
      el.style.transform = `rotate(${deg}deg)`;
      if (ball) {
        ball.style.transition = reduced ? "transform 200ms linear" : "transform 4.2s cubic-bezier(0.05, 0.6, 0.15, 1)";
        ball.style.transform = `rotate(${extra * 1.35}deg)`;
      }
    });
    const t = window.setTimeout(() => {
      if (ball) {
        ball.style.transition = "transform 280ms ease-out";
        ball.style.transform = "rotate(0deg)";
      }
      doneRef.current();
    }, wait);
    return () => {
      window.cancelAnimationFrame(frame);
      window.clearTimeout(t);
    };
  }, [reduced, spinning, target]);

  return (
    <div className="op-wheel-wrap">
      <div className="op-wheel-stage">
        <div ref={ballRef} className="op-ball-ring" aria-hidden>
          <div className="op-ball" />
        </div>
        <div
          ref={wheelRef}
          className="op-wheel"
          style={{ background: `conic-gradient(${wheelBackground()})` }}
          role="img"
          aria-label={target != null ? `Колесо, результат ${target}` : "Колесо рулетки"}
        />
      </div>
    </div>
  );
}
