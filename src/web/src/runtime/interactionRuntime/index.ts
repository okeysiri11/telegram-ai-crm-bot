/**
 * Enterprise Interaction Runtime public API — Sprint 29.6.
 */

export {
  INTERACTION_RUNTIME_VERSION,
  INTERACTION_PERSIST_KEY,
  INTERACTION_API_PREFIX,
} from "./interactionTypes";
export type {
  InteractionObjectKind,
  InteractionActionId,
  InteractionEventName,
  SelectionMode,
  InteractionTarget,
  ContextActionDef,
  InteractionContext,
  InteractionSession,
  InteractionHistoryEntry,
  SelectionState,
  NavigationEntry,
  SearchHit,
  ActionResult,
} from "./interactionTypes";

export { interactionEvents, publishInteractionEvent } from "./interactionEvents";
export { interactionPermissions } from "./interactionPermissions";
export type { InteractionPermissionScope } from "./interactionPermissions";
export { interactionRegistry } from "./interactionRegistry";
export { interactionSessionStore, interactionHistory } from "./interactionSession";
export { selectionEngine } from "./selectionEngine";
export { navigationEngine, buildObjectCatalog } from "./navigationEngine";
export { interactionCache } from "./interactionCache";
export { executeContextAction, contextActionsForTarget } from "./contextActions";
export { interactionRuntime } from "./interactionRuntime";
export { interactionRuntimeApi, interactionApiPrefix } from "./interactionRuntimeApi";
