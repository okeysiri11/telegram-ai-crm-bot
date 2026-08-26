import { useRoomTransition } from "./useRoomTransition";

export { useRoomTransition };

export function RoomTransition({ phase }: { phase: "idle" | "leaving" | "entering" }) {
  if (phase === "idle") return null;
  return (
    <div className={`op-transition is-${phase}`} data-testid="room-transition" aria-hidden>
      <span className="op-transition-veil" />
      <span className="op-transition-brass" />
      <span className="op-transition-pool" />
    </div>
  );
}

export function RoomTransitionHost() {
  const { phase } = useRoomTransition();
  return <RoomTransition phase={phase} />;
}
