import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { casinoSound } from "../casinoSound";
import {
  HALL_ART,
  HALL_ENTER_MS,
  HALL_ZONES,
  hallZoneById,
  polygonClipPath,
  polygonPoints,
  type HallZone,
} from "./hallZones";

function prefersReducedMotion(): boolean {
  return typeof window !== "undefined" && Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches);
}

function isCoarsePointer(): boolean {
  return typeof window !== "undefined" && Boolean(window.matchMedia?.("(pointer: coarse)")?.matches);
}

export function LobbyHall() {
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
  const focus = hallZoneById(focusId);
  const scale = prefersReducedMotion() ? 1 : entering ? 1.055 : focus ? 1.035 : 1;

  function setActive(id: string | null) {
    setActiveId((cur) => (cur === id ? cur : id));
  }

  function enter(zone: HallZone) {
    if (enteringRef.current) return;
    casinoSound.door();
    if (prefersReducedMotion()) {
      navigate(zone.route);
      return;
    }
    setEntering(zone.id);
    setActive(zone.id);
    enterTimer.current = window.setTimeout(() => navigate(zone.route), HALL_ENTER_MS);
  }

  function activate(zone: HallZone) {
    if (enteringRef.current) return;
    if (isCoarsePointer() && activeId !== zone.id) {
      setActive(zone.id);
      casinoSound.hover();
      return;
    }
    enter(zone);
  }

  return (
    <div
      className={`op-hall-stage${focus ? " is-focused" : ""}${entering ? " is-entering" : ""}${debug ? " is-debug" : ""}`}
      data-testid="lobby-hall-stage"
      data-hall-active={focusId ?? ""}
      style={{
        ["--hall-x" as string]: String(focus?.focus.x ?? 50),
        ["--hall-y" as string]: String(focus?.focus.y ?? 50),
        ["--hall-s" as string]: String(scale),
      }}
    >
      <img
        className="op-lobby-photo op-hall-art"
        src={HALL_ART.src}
        width={HALL_ART.width}
        height={HALL_ART.height}
        alt=""
        decoding="async"
        draggable={false}
      />
      <div className="op-hall-veil" aria-hidden />
      <svg
        className={`op-hall-glow${debug ? " is-debug" : ""}`}
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        aria-hidden
      >
        {HALL_ZONES.map((zone) => (
          <polygon
            key={zone.id}
            points={polygonPoints(zone.polygon)}
            className={`op-hall-shape is-${zone.id}${focusId === zone.id ? " is-on" : ""}${entering === zone.id ? " is-entering" : ""}`}
          />
        ))}
        {debug
          ? HALL_ZONES.map((zone) => (
              <text key={`dbg-${zone.id}`} className="op-hall-debug-id" x={zone.labelAt.x} y={zone.labelAt.y}>
                {zone.id}
              </text>
            ))
          : null}
      </svg>
      {HALL_ZONES.map((zone) => (
        <button
          key={zone.id}
          type="button"
          className={`op-hall-hit is-${zone.id}${activeId === zone.id || entering === zone.id ? " is-active is-lit" : ""}`}
          style={{ clipPath: polygonClipPath(zone.polygon), zIndex: zone.zIndex }}
          data-testid={`hotspot-${zone.id}`}
          aria-label={`${zone.label}. ${zone.cta}`}
          onPointerEnter={() => {
            if (enteringRef.current) return;
            if (activeId !== zone.id) casinoSound.hover();
            setActive(zone.id);
          }}
          onPointerLeave={() => {
            if (enteringRef.current) return;
            setActiveId((cur) => (cur === zone.id ? null : cur));
          }}
          onFocus={() => setActive(zone.id)}
          onBlur={() => {
            if (enteringRef.current) return;
            setActiveId((cur) => (cur === zone.id ? null : cur));
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              enter(zone);
            }
          }}
          onClick={() => activate(zone)}
        />
      ))}
      {focus ? (
        <div
          className="op-hall-label"
          data-testid="hall-zone-label"
          style={{ left: `${focus.labelAt.x}%`, top: `${focus.labelAt.y}%` }}
        >
          <strong>{focus.label}</strong>
          <small>{focus.sublabel}</small>
          <span>{focus.cta} →</span>
        </div>
      ) : null}
    </div>
  );
}
