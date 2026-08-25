import { Outlet } from "react-router-dom";
import { RoomTransition } from "../transitions/RoomTransition";
import { useRoomTransition } from "../transitions/useRoomTransition";

export function RoomStage() {
  const { phase } = useRoomTransition();
  return (
    <div className="op-room-stage" data-testid="room-stage">
      <RoomTransition phase={phase} />
      <Outlet />
    </div>
  );
}
