import { HALL_ART } from "./hallZones";
import { SlotsChairSvg } from "./SlotsChairSvg";
import { SLOTS_GOLD_EDGE, SLOTS_MASK } from "./slotRightMask";

type Props = {
  active: boolean;
};

/** Locked machine gold PNG plus open-path chair rims. Same SLOTS hover flag. */
export function SlotsPhotoOverlay({ active }: Props) {
  return (
    <>
      <img
        className={`op-slots-photo${active ? " is-on" : ""}`}
        data-testid="slots-photo-overlay"
        data-slot-mask-ready="true"
        data-slots-hovered={active ? "true" : "false"}
        src={SLOTS_GOLD_EDGE.src}
        width={SLOTS_GOLD_EDGE.width}
        height={SLOTS_GOLD_EDGE.height}
        alt=""
        aria-hidden
        draggable={false}
      />
      <SlotsChairSvg active={active} />
    </>
  );
}

export function SlotsMaskDebugInspector() {
  return (
    <div className="op-slots-mask-debug" data-testid="slots-mask-debug">
      <figure>
        <img src={HALL_ART.src} width={HALL_ART.width} height={HALL_ART.height} alt="" />
        <figcaption>original hall</figcaption>
      </figure>
      <figure className="is-checker">
        <img src={SLOTS_MASK.src} width={SLOTS_MASK.width} height={SLOTS_MASK.height} alt="" />
        <figcaption>foreground PNG</figcaption>
      </figure>
      <figure className="is-tint">
        <img src={HALL_ART.src} width={HALL_ART.width} height={HALL_ART.height} alt="" />
        <img className="op-slots-mask-debug-tint" src={SLOTS_MASK.src} width={SLOTS_MASK.width} height={SLOTS_MASK.height} alt="" />
        <figcaption>magenta 65% on hall</figcaption>
      </figure>
    </div>
  );
}
