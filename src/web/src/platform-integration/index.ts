/** Sprint 30.6 — Enterprise Platform Integration. */
export {
  PLATFORM_BOOT_VERSION,
  BOOT_ENTRY_ROUTES,
  INTEGRATION_ROUTES,
  ROUTE_ALIASES,
  requiredBootPaths,
  assertBootCoverage,
  bootRouteIds,
} from "./platformBoot";
export { OWNER_SUBSYSTEMS } from "./ownerSubsystems";
export { BETA_LIVE_DEMO_STEPS, BETA_LIVE_DEMO_META } from "./betaLiveDemo";
export { derivePlatformHealth } from "./platformHealth";
export type { PlatformHealthSnapshot } from "./platformHealth";
export { PlatformHealthPage } from "./PlatformHealthPage";
export { PlatformErrorPage } from "./PlatformErrorPage";
export type { PlatformErrorKind } from "./PlatformErrorPage";
