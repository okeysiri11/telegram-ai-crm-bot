import type { ReactNode } from "react";
import { useIsMobile } from "./useIsMobile";

/** Width ≤768px uses the mobile surface; desktop keeps the existing layout. Same APIs. */
export function MobileRouteGate({
  mobile,
  desktop,
}: {
  mobile: ReactNode;
  desktop: ReactNode;
}) {
  return useIsMobile() ? <>{mobile}</> : <>{desktop}</>;
}
