import { useRoomTransition } from "./useRoomTransition";

export { useRoomTransition };

export function RoomTransition({ phase }: { phase: "idle" | "leaving" | "entering" }) {
  if (phase === "idle") return null;
  return (
    <div className={`op-transition is-${phase}`} data-testid="room-transition" aria-hidden>
      <span className="op-transition-veil" />
    </div>
  );
}
