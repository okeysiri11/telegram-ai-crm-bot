import { Navigate } from "react-router-dom";
import { ControlCenterStudio } from "../god-mode/ControlCenterStudio";
import { useIsPlatformOwner } from "../managers/platformOwner";

export function GodModePage() {
  const owner = useIsPlatformOwner();
  if (!owner) {
    return <Navigate to="/platform-builder" replace />;
  }
  return <ControlCenterStudio />;
}
