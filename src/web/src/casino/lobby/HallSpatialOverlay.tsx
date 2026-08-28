import { memo, useEffect, useRef, useState, type RefObject } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { casinoSound } from "../casinoSound";
import {
  HALL_ENTER_MS,
  HALL_ZONES,
  clampTooltip,
  hallZoneById,
  polygonPoints,
  zoneVisuals,
  type HallZone,
} from "./hallZones";

function prefersReducedMotion(): boolean {
  return typeof window !== "undefined" && Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches);
}

function isCoarsePointer(): boolean {
  return typeof window !== "undefined" && Boolean(window.matchMedia?.("(pointer: coarse)")?.matches);
}

function applyStageFocus(
  stage: HTMLElement | null,
  focus: HTMLElement | null,
  zone: HallZone | undefined,
  entering: boolean,
) {
  const reduced = prefersReducedMotion();
  const scale = reduced ? 1 : entering ? 1.015 : zone ? 1.012 : 1;
  const x = String(zone?.focus.x ?? 50);
  const y = String(zone?.focus.y ?? 50);
  for (const el of [stage, focus]) {
    if (!el) continue;
    el.style.setProperty("--hall-s", String(scale));
    el.style.setProperty("--hall-x", x);
    el.style.setProperty("--hall-y", y);
    el.classList.toggle("is-focused", Boolean(zone));
    el.classList.toggle("is-entering", entering);
  }
  if (stage) stage.dataset.hallActive = zone?.id ?? "";
}

type OverlayProps = {
  stageRef: RefObject<HTMLDivElement | null>;
  focusRef: RefObject<HTMLDivElement | null>;
};

function HallSpatialOverlayInner({ stageRef, focusRef }: OverlayProps) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const debug = import.meta.env.DEV && params.get("casinoHotspots") === "debug";
  const [activeId, setActiveId] = useState<string | null>(null);
  const [entering, setEntering] = useState<string | null>(null);
  const enterTimer = useRef<number | null>(null);
  const enteringRef = useRef<string | null>(null);

  useEffect(() => {
    enteringRef.current = entering;
  }, [entering]);

  useEffect(
    () => () => {
      if (enterTimer.current != null) window.clearTimeout(enterTimer.current);
    },
    [],
  );

  const focusId = entering ?? activeId;
  const zone = hallZoneById(focusId);

  useEffect(() => {
    applyStageFocus(stageRef.current, focusRef.current, zone, Boolean(entering));
  }, [entering, focusRef, stageRef, zone]);

  function setActive(id: string | null) {
    setActiveId((cur) => (cur === id ? cur : id));
  }

  function enter(next: HallZone) {
    if (enteringRef.current) return;
    casinoSound.door();
    if (prefersReducedMotion()) {
      navigate(next.route);
      return;
    }
    setEntering(next.id);
    setActive(next.id);
    enterTimer.current = window.setTimeout(() => navigate(next.route), HALL_ENTER_MS);
  }

  function activate(next: HallZone) {
    if (enteringRef.current) return;
    if (isCoarsePointer() && activeId !== next.id) {
      setActive(next.id);
      casinoSound.hover();
      return;
    }
    enter(next);
  }

  const tip = zone ? clampTooltip(zone.tooltip.x, zone.tooltip.y) : null;

  return (
    <div
      className="op-hall-overlay"
      data-testid="hall-spatial-overlay"
      data-active-zone={focusId ?? ""}
      data-idle={focusId ? "false" : "true"}
    >
      <svg
        className={`op-hall-glow${debug ? " is-debug" : ""}`}
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        aria-hidden
        data-testid="hall-visual-layer"
      >
        <defs>
          <filter id="op-hall-gold-glow" x="-12%" y="-12%" width="124%" height="124%">
            <feGaussianBlur stdDeviation="0.22" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {HALL_ZONES.map((item) =>
          zoneVisuals(item).map((visual, index) => {
            const on = focusId === item.id;
            const role = visual.role ?? "rim";
            return (
              <polygon
                key={`${item.id}-glow-${index}`}
                points={polygonPoints(visual.polygon)}
                fill="none"
                stroke={on ? undefined : "none"}
                data-visual-zone={item.id}
                data-visual-role={role}
                data-visual-on={on ? "true" : "false"}
                className={`op-hall-shape is-${item.id} is-${role}${on ? " is-on" : ""}${entering === item.id ? " is-entering" : ""}`}
              />
            );
          }),
        )}
        {debug
          ? HALL_ZONES.map((item) => (
              <text key={`dbg-${item.id}`} className="op-hall-debug-id" x={item.tooltip.x} y={item.tooltip.y}>
                {item.id}
              </text>
            ))
          : null}
      </svg>
      {HALL_ZONES.map((item) => (
        <div
          key={item.id}
          role="button"
          tabIndex={0}
          className={`op-hall-zone is-${item.id}${activeId === item.id || entering === item.id ? " is-active is-lit" : ""}`}
          style={{ zIndex: item.zIndex }}
          data-testid={`hotspot-${item.id}`}
          aria-label={`${item.label}. ${item.cta}`}
          onPointerEnter={() => {
            if (enteringRef.current) return;
            if (activeId !== item.id) casinoSound.hover();
            setActive(item.id);
          }}
          onPointerLeave={() => {
            if (enteringRef.current) return;
            setActiveId((cur) => (cur === item.id ? null : cur));
          }}
          onFocus={() => setActive(item.id)}
          onBlur={() => {
            if (enteringRef.current) return;
            setActiveId((cur) => (cur === item.id ? null : cur));
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              enter(item);
            }
          }}
          onClick={() => activate(item)}
        >
          {item.polygons.map((polygon, index) => (
            <span
              key={`${item.id}-hit-${index}`}
              className="op-hall-hit"
              style={{ clipPath: `polygon(${polygon.map(([x, y]) => `${x}% ${y}%`).join(", ")})` }}
            />
          ))}
        </div>
      ))}
      {zone && tip ? (
        <div
          className={`op-hall-label is-${zone.tooltip.align}`}
          data-testid="hall-zone-label"
          data-tooltip-zone={zone.id}
          style={{ left: `${tip.x}%`, top: `${tip.y}%` }}
        >
          <strong>{zone.label}</strong>
          <small>{zone.sublabel}</small>
          <span>{zone.cta} →</span>
        </div>
      ) : null}
    </div>
  );
}

export const HallSpatialOverlay = memo(HallSpatialOverlayInner);
