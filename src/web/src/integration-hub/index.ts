/** Enterprise Integration Hub — Sprint 28.0. */
export {
  INTEGRATION_HUB_VERSION,
  OS_DEEP_LINKS,
  surfaceFromPath,
  buildDeepLink,
  parseDeepLink,
  type SharedAppContext,
  type EnterpriseEvent,
  type EnterpriseEventType,
  type OsSurfaceId,
  type DeepLinkTarget,
} from "./types";
export { enterpriseEventBus } from "./enterpriseEventBus";
export { useIntegrationContext } from "./integrationContextStore";
export { sessionCoordinator, type SessionRestoreReport } from "./sessionCoordinator";
export { registerIntegrationSearch } from "./searchRegistration";
export {
  useIntegrationBoot,
  useSharedContext,
  useIntegrationRuntimeHealth,
  useIntegrationNotifications,
  useIntegrationNavigate,
} from "./useIntegrationHub";
