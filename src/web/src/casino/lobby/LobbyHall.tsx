import { useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { HALL_ART } from "./hallZones";
import { HallSpatialOverlay } from "./HallSpatialOverlay";
import { SlotsMaskDebugInspector } from "./SlotRightHover";

export function LobbyHall() {
  const stageRef = useRef<HTMLDivElement>(null);
  const focusRef = useRef<HTMLDivElement>(null);
  const [params] = useSearchParams();
  const maskDebug = import.meta.env.DEV && params.get("casinoMaskDebug") === "slots";

  return (
    <div
      ref={stageRef}
      className="op-hall-stage"
      data-testid="lobby-hall-stage"
      data-hall-active=""
      data-hall-full-width="true"
      data-hall-fit="contain"
    >
      {maskDebug ? <SlotsMaskDebugInspector /> : null}
      <div ref={focusRef} className="op-hall-fit op-hall-focus" data-testid="hall-image-wrap">
        <img
          className="op-lobby-photo op-hall-art"
          src={HALL_ART.src}
          width={HALL_ART.width}
          height={HALL_ART.height}
          alt=""
          decoding="async"
          draggable={false}
        />
        <HallSpatialOverlay stageRef={stageRef} focusRef={focusRef} />
      </div>
    </div>
  );
}
