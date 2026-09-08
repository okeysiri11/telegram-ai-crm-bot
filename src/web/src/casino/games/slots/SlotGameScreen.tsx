import { useMemo } from "react";
import { Navigate, useParams } from "react-router-dom";
import { getSlotDefinition } from "./slotCatalog";
import { SeatedSlotCabinet } from "./SeatedSlotCabinet";
import "./slotsHall.css";

export function SlotGameScreen() {
  const { machineId = "" } = useParams();
  const def = useMemo(() => getSlotDefinition(machineId), [machineId]);
  if (!def) return <Navigate to="/casino/slots" replace />;
  return <SeatedSlotCabinet def={def} />;
}

export default SlotGameScreen;
