import { memo, useEffect, useRef, useState, type RefObject } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { casinoSound } from "../casinoSound";
import {
  HALL_ART,
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
  const scale = reduced ? 1 : entering ? 1.015 : zone ? 1.01 : 1;
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
  const masks = zone ? zoneVisuals(zone) : [];
  const signMasks = masks.filter((item) => item.role === "sign");
  const hotMasks = masks.filter((item) => item.role === "lamp" || item.role === "pulse");

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
        className={`op-hall-lit${focusId ? " is-on" : ""}`}
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        aria-hidden
        data-testid="hall-lit-overlay"
        data-lit-zone={focusId ?? ""}
      >
        <defs>
          <filter id="op-hall-mask-feather" x="-8%" y="-8%" width="116%" height="116%">
            <feGaussianBlur stdDeviation="0.32" />
          </filter>
          <linearGradient id="op-hall-sweep-g" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="rgba(255,210,115,0)" />
            <stop offset="0.48" stopColor="rgba(255,210,115,0.55)" />
            <stop offset="1" stopColor="rgba(255,210,115,0)" />
          </linearGradient>
          <mask id="op-hall-object-mask" maskUnits="userSpaceOnUse">
            <rect width="100" height="100" fill="black" />
            <g filter="url(#op-hall-mask-feather)">
              {masks.map((visual, index) => (
                <polygon
                  key={`${zone?.id}-mask-${index}`}
                  points={polygonPoints(visual.polygon)}
                  fill="white"
                  stroke="none"
                  data-visual-zone={zone?.id}
                  data-visual-role={visual.role ?? "object"}
                  data-visual-on="true"
                  className={`op-hall-mask is-${zone?.id} is-${visual.role ?? "object"}`}
                />
              ))}
            </g>
          </mask>
          <mask id="op-hall-sign-mask" maskUnits="userSpaceOnUse">
            <rect width="100" height="100" fill="black" />
            <g filter="url(#op-hall-mask-feather)">
              {signMasks.map((visual, index) => (
                <polygon
                  key={`${zone?.id}-sign-${index}`}
                  points={polygonPoints(visual.polygon)}
                  fill="white"
                  stroke="none"
                />
              ))}
            </g>
          </mask>
          <mask id="op-hall-hot-mask" maskUnits="userSpaceOnUse">
            <rect width="100" height="100" fill="black" />
            <g filter="url(#op-hall-mask-feather)">
              {hotMasks.map((visual, index) => (
                <polygon
                  key={`${zone?.id}-hot-${index}`}
                  points={polygonPoints(visual.polygon)}
                  fill="white"
                  stroke="none"
                />
              ))}
            </g>
          </mask>
        </defs>
        {focusId ? (
          <>
            <image
              href={HALL_ART.src}
              x="0"
              y="0"
              width="100"
              height="100"
              preserveAspectRatio="none"
              mask="url(#op-hall-object-mask)"
              className="op-hall-lit-photo"
            />
            <rect
              width="100"
              height="100"
              fill="rgba(255, 210, 115, 0.18)"
              mask="url(#op-hall-object-mask)"
              className="op-hall-lit-gold"
            />
            {signMasks.length ? (
              <rect
                width="100"
                height="100"
                fill="rgba(245, 174, 55, 0.28)"
                mask="url(#op-hall-sign-mask)"
                className="op-hall-lit-sign"
              />
            ) : null}
            {hotMasks.length ? (
              <rect
                width="100"
                height="100"
                fill="rgba(255, 210, 115, 0.22)"
                mask="url(#op-hall-hot-mask)"
                className="op-hall-lit-hot"
              />
            ) : null}
            <rect
              className="op-hall-sweep"
              x="-30"
              y="0"
              width="40"
              height="100"
              fill="url(#op-hall-sweep-g)"
              mask="url(#op-hall-object-mask)"
            />
          </>
        ) : null}
      </svg>
      {debug ? (
        <svg
          className="op-hall-glow is-debug"
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          aria-hidden
          data-testid="hall-visual-layer"
        >
          {HALL_ZONES.map((item) =>
            zoneVisuals(item).map((visual, index) => (
              <polygon
                key={`${item.id}-dbg-${index}`}
                points={polygonPoints(visual.polygon)}
                className={`op-hall-debug-shape is-${item.id}`}
              />
            )),
          )}
          {HALL_ZONES.map((item) => (
            <text key={`dbg-${item.id}`} className="op-hall-debug-id" x={item.tooltip.x} y={item.tooltip.y}>
              {item.id}
            </text>
          ))}
        </svg>
      ) : (
        <svg className="op-hall-glow" viewBox="0 0 100 100" aria-hidden data-testid="hall-visual-layer" />
      )}
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
